import json
import sqlite3
import unicodedata
from collections import deque
from pathlib import Path
from typing import Deque, Optional

import requests

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.infra.init_db import (
    DB_PATH,
    _compute_digit_stats,
    _compute_qdls,
    _count_isolated,
    _max_consecutive_run,
    _max_jump,
)

API_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/diadesorte"


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower().strip()


MONTH_NAME_TO_NUMBER = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def _get_month_number(month_name: str) -> int:
    normalized = _normalize_text(month_name)
    if normalized not in MONTH_NAME_TO_NUMBER:
        raise ValueError(f"Nome de mes desconhecido: {month_name!r}")
    return MONTH_NAME_TO_NUMBER[normalized]


def _fetch_json(url: str) -> dict:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def _fetch_latest_contest_number() -> int:
    payload = _fetch_json(API_BASE)
    return int(payload["numero"])


def _fetch_contest(number: int) -> dict:
    return _fetch_json(f"{API_BASE}/{number}")


def _extract_balls(payload: dict) -> list[int]:
    dezenas = payload.get("listaDezenas") or payload.get("dezenasSorteadasOrdemSorteio")
    if not dezenas:
        raise ValueError("Payload nao contem dezenas sorteadas.")
    return sorted(int(value) for value in dezenas)


def _extract_ganhadores(payload: dict) -> int:
    for faixa in payload.get("listaRateioPremio", []):
        if _normalize_text(faixa.get("descricaoFaixa", "")) == "7 acertos":
            return int(faixa.get("numeroDeGanhadores", 0))
    return 0


def _compute_nah(curr: set[int], history: Deque[set[int]]) -> tuple[Optional[int], Optional[int], Optional[int]]:
    if not history:
        return None, None, None

    ultimo = history[-1]
    penultimo = history[-2] if len(history) >= 2 else None

    novos = curr - ultimo
    if penultimo:
        atuais = (curr & ultimo) - penultimo
        hits = curr & ultimo & penultimo
    else:
        atuais = curr & ultimo
        hits = set()

    return len(novos), len(atuais), len(hits)


def _load_existing_history(cur: sqlite3.Cursor) -> tuple[int, Deque[set[int]]]:
    cur.execute(
        """
        SELECT concurso, bola1, bola2, bola3, bola4, bola5, bola6, bola7
        FROM dia_da_sorte_results
        ORDER BY concurso
        """
    )
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError("Tabela dia_da_sorte_results esta vazia.")

    last_contest = int(rows[-1][0])
    history: Deque[set[int]] = deque(maxlen=2)

    for row in rows[-2:]:
        bolas = {int(value) for value in row[1:]}
        history.append(bolas)

    return last_contest, history


def _build_membership_sum(values: list[int]) -> tuple[str, list[int]]:
    if not values:
        return "0", []
    exprs = [f"CASE WHEN ? IN (d1,d2,d3,d4,d5,d6,d7) THEN 1 ELSE 0 END" for _ in values]
    return " + ".join(exprs), values


def _update_bets_nah(
    cur: sqlite3.Cursor,
    ultimo: list[int],
    penultimo: Optional[list[int]],
) -> None:
    if not ultimo:
        cur.execute("UPDATE dia_da_sorte_bets SET nah_n = NULL, nah_a = NULL, nah_h = NULL")
        return

    ultimo_sorted = sorted(ultimo)
    ambos_sorted = sorted(set(ultimo) & set(penultimo or []))

    common_last_expr, params_last = _build_membership_sum(ultimo_sorted)
    common_both_expr, params_both = _build_membership_sum(ambos_sorted)

    nah_n_expr = f"7 - ({common_last_expr})"
    nah_a_expr = f"({common_last_expr}) - ({common_both_expr})"
    nah_h_expr = common_both_expr

    sql = f"""
        UPDATE dia_da_sorte_bets
        SET
            nah_n = {nah_n_expr},
            nah_a = {nah_a_expr},
            nah_h = {nah_h_expr}
    """

    params: list[int] = []
    if params_last:
        params.extend(params_last)  # nah_n
        params.extend(params_last)  # nah_a (common_last)
    if params_both:
        params.extend(params_both)  # nah_a (common_both)
        params.extend(params_both)  # nah_h

    cur.execute(sql, params)


def _build_insert_payload(
    payload: dict,
    history: Deque[set[int]],
) -> tuple:
    bolas = _extract_balls(payload)
    curr_set = set(bolas)

    pares = sum(1 for value in bolas if value % 2 == 0)
    impares = len(bolas) - pares

    nah_n, nah_a, nah_h = _compute_nah(curr_set, history)

    qdls = _compute_qdls(bolas)
    digit_stats = _compute_digit_stats(bolas)

    return (
        int(payload["numero"]),
        payload["dataApuracao"],
        *bolas,
        _get_month_number(payload["nomeTimeCoracaoMesSorte"]),
        _extract_ganhadores(payload),
        pares,
        impares,
        nah_n,
        nah_a,
        nah_h,
        _max_consecutive_run(bolas),
        _max_jump(bolas),
        _count_isolated(bolas),
        json.dumps(qdls),
        json.dumps(digit_stats),
    )


def update_results() -> list[int]:
    db_path = Path(DB_PATH)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        last_contest, history = _load_existing_history(cur)
        latest_remote = _fetch_latest_contest_number()

        if latest_remote <= last_contest:
            return []

        inserted = []
        for contest in range(last_contest + 1, latest_remote + 1):
            payload = _fetch_contest(contest)
            row = _build_insert_payload(payload, history)

            cur.execute(
                """
                INSERT INTO dia_da_sorte_results (
                    concurso, data_sorteio,
                    bola1, bola2, bola3, bola4, bola5, bola6, bola7,
                    mes_da_sorte, ganhadores_7_acertos,
                    pares, impares,
                    nah_n, nah_a, nah_h,
                    max_consec, maior_salto, isoladas,
                    qdls, digit_stats
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                row,
            )

            history.append(set(row[2:9]))
            inserted.append(contest)

        if inserted:
            hist_list = list(history)
            ultimo = sorted(hist_list[-1])
            penultimo = sorted(hist_list[-2]) if len(hist_list) >= 2 else None
            _update_bets_nah(cur, ultimo, penultimo)
            conn.commit()

        return inserted


def main() -> None:
    inserted = update_results()
    if not inserted:
        print("Nenhum novo concurso encontrado.")
    else:
        print(f"Foram inseridos {len(inserted)} concursos: {', '.join(map(str, inserted))}")


if __name__ == "__main__":
    main()
