import sqlite3
import unicodedata
from pathlib import Path
from typing import Optional

import requests

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.infra.init_db import DB_PATH

API_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower().strip()


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
        if _normalize_text(faixa.get("descricaoFaixa", "")) == "15 acertos":
            return int(faixa.get("numeroDeGanhadores", 0))
    return 0


def _load_last_contest(cur: sqlite3.Cursor) -> Optional[int]:
    cur.execute("SELECT concurso FROM results ORDER BY concurso DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        return None
    return int(row[0])


def update_results() -> list[int]:
    db_path = Path(DB_PATH)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        last_contest = _load_last_contest(cur)
        if last_contest is None:
            raise RuntimeError("Tabela results esta vazia. Execute init_db primeiro.")

        latest_remote = _fetch_latest_contest_number()
        if latest_remote <= last_contest:
            return []

        inserted: list[int] = []
        for contest in range(last_contest + 1, latest_remote + 1):
            payload = _fetch_contest(contest)
            dezenas = _extract_balls(payload)
            if len(dezenas) != 15:
                raise ValueError(f"Concurso {contest} retornou {len(dezenas)} dezenas.")
            data_apuracao = payload.get("dataApuracao") or ""
            ganhadores = _extract_ganhadores(payload)

            row = (
                contest,
                data_apuracao,
                *dezenas,
                ganhadores,
            )
            cur.execute(
                "INSERT OR REPLACE INTO results ("
                "concurso, data, "
                "n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, "
                "ganhador"
                ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                row,
            )
            inserted.append(contest)

        if inserted:
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
