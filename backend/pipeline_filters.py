from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple, Optional


def dezenas_from_row(row: dict) -> List[int]:
    return [row[f'n{i}'] for i in range(1, 16)]


def count_par_impar(dezenas: Sequence[int]) -> Tuple[int, int]:
    pares = sum(1 for d in dezenas if d % 2 == 0)
    return pares, len(dezenas) - pares


def max_jump(dezenas: Sequence[int]) -> int:
    s = sorted(dezenas)
    if len(s) < 2:
        return 0
    return max(s[i+1] - s[i] for i in range(len(s) - 1))


def longest_consecutive_run(dezenas: Sequence[int]) -> int:
    s = sorted(dezenas)
    if not s:
        return 0
    best = 1
    run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            run += 1
            if run > best:
                best = run
        elif s[i] == s[i - 1]:
            # ignore duplicates defensively
            continue
        else:
            run = 1
    return best


def count_columns(dezenas: Sequence[int]) -> List[int]:
    # Columns of 5x5 grid: 1,6,11,16,21 | 2,7,12,17,22 | ...
    cols = [0, 0, 0, 0, 0]
    for d in dezenas:
        c = (d - 1) % 5
        cols[c] += 1
    return cols


def count_cre(dezenas: Sequence[int]) -> int:
    # Count consecutive equal row patterns between adjacent lines
    # Determine row and column for each dezena in 5x5 grid
    rows_positions: List[List[int]] = [[] for _ in range(5)]
    for d in dezenas:
        r = (d - 1) // 5  # 0..4
        c = ((d - 1) % 5) + 1  # 1..5
        rows_positions[r].append(c)
    rows_positions = [sorted(lst) for lst in rows_positions]
    return sum(1 for i in range(4) if rows_positions[i] == rows_positions[i + 1])


def has_run_len_at_least(dezenas: Sequence[int], min_len: int) -> bool:
    s = sorted(dezenas)
    run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1] + 1:
            run += 1
            if run >= min_len:
                return True
        else:
            run = 1
    return False


def has_line_three_consecutives_3L(dezenas: Sequence[int]) -> bool:
    """Notebook rule (03/2024):
    Considering base 3-por-linha, sort the 15 dezenas and split into 5 chunks of 3.
    Return True if any chunk has exactly 3 consecutive numbers (x, x+1, x+2).
    """
    s = sorted(dezenas)
    for i in range(0, 15, 3):
        linha = s[i:i + 3]
        if len(linha) == 3 and linha[1] == linha[0] + 1 and linha[2] == linha[0] + 2:
            return True
    return False


# --- Additional filters (7–11) ---

def bola_da_vez(
    dezenas: Sequence[int],
    entram: Optional[Sequence[int]] = None,
    saem: Optional[Sequence[int]] = None,
) -> bool:
    """True if at least one prediction is correct:
    - any number from `entram` is present in `dezenas`; or
    - any number from `saem` is absent from `dezenas`.
    """
    s = set(dezenas)
    acertou_entram = bool(entram and (set(entram) & s))
    acertou_saem = bool(saem and (set(saem) - s))
    return acertou_entram or acertou_saem


def in_losango_ou_centro(dezenas: Sequence[int]) -> bool:
    """Keep if contains center (13) or any from the immediate diamond ring around: {8,12,14,18}."""
    s = set(dezenas)
    center = {13}
    ring1 = {8, 12, 14, 18}
    return bool((center | ring1) & s)


def count_in_range(dezenas: Sequence[int], low: int, high: int) -> int:
    return sum(1 for d in dezenas if low <= d <= high)


def maximo_um_cinco(dezenas: Sequence[int]) -> bool:
    """Notebook rule: in countC vector, value 5 appears at most once."""
    cols = count_columns(dezenas)
    return cols.count(5) <= 1


def minimo_um_quatro(dezenas: Sequence[int]) -> bool:
    """Notebook rule: in countC vector, value 4 appears at least once."""
    cols = count_columns(dezenas)
    return cols.count(4) >= 1


def tem_dezena_onze_ou_quinze(dezenas: Sequence[int]) -> bool:
    return bool(set(dezenas) & {11, 15})


def countcs_em_valores(dezenas: Sequence[int], permitidos: Sequence[int] = (2, 3, 4, 5)) -> bool:
    return longest_consecutive_run(dezenas) in set(permitidos)


def filtro_cantos(dezenas: Sequence[int], minimo: int = 2) -> bool:
    cantos = {1, 5, 21, 25}
    return sum(1 for d in dezenas if d in cantos) >= minimo


def filtro_diagonais(dezenas: Sequence[int]) -> bool:
    grupo_1 = {5, 9, 17, 21}
    grupo_2 = {1, 7, 19, 25}
    s = set(dezenas)
    return bool(s & grupo_1) and sum(1 for d in grupo_2 if d in s) >= 2


def _compute_bola_da_vez_stats(hist_rows: Sequence[dict]) -> Dict[int, Dict[str, int]]:
    """Compute per-number streak/delay/frequency stats over historical draws."""
    stats: Dict[int, Dict[str, int]] = {
        n: {
            'frequencia': 0,
            'sequencia_atual': 0,
            'maior_sequencia': 0,
            'atraso_atual': 0,
            'maior_atraso': 0,
        }
        for n in range(1, 26)
    }

    for row in hist_rows:
        dezenas = {row[f'n{i}'] for i in range(1, 16)}
        for n in range(1, 26):
            st = stats[n]
            if n in dezenas:
                st['frequencia'] += 1
                st['sequencia_atual'] += 1
                if st['sequencia_atual'] > st['maior_sequencia']:
                    st['maior_sequencia'] = st['sequencia_atual']
                st['atraso_atual'] = 0
            else:
                st['atraso_atual'] += 1
                if st['atraso_atual'] > st['maior_atraso']:
                    st['maior_atraso'] = st['atraso_atual']
                st['sequencia_atual'] = 0

    return stats


def compute_bola_da_vez_listas(
    hist_rows: Sequence[dict],
    margem_entram: int = 4,
    margem_saem: int = 9,
) -> Tuple[List[int], List[int]]:
    """Derive bola-da-vez lists using Top-3 heuristics.

    Current rule:
    - The reference draw is the latest row in `hist_rows` (cutoff used by
      each backtest line).
    - `entram`: top 3 by `maior_atraso` (tie-break: atraso atual, numero),
      considering only dezenas NOT present in the reference draw.
    - `saem`: top 3 by `frequencia` (tie-break: sequencia atual, numero),
      considering only dezenas present in the reference draw.

    Notes:
    - `margem_entram` and `margem_saem` are kept for backward compatibility
      but are no longer used.
    """
    if not hist_rows:
        return [], []

    referencia_row = hist_rows[-1]
    stats = _compute_bola_da_vez_stats(hist_rows)
    top_n = 3

    ultimo_sorteio = {int(referencia_row[f'n{i}']) for i in range(1, 16)}
    candidatas_entram = set(range(1, 26)) - ultimo_sorteio
    candidatas_saem = set(ultimo_sorteio)

    ordenado_atraso = sorted(
        [(n, st) for n, st in stats.items() if n in candidatas_entram],
        key=lambda it: (-it[1]['maior_atraso'], -it[1]['atraso_atual'], it[0]),
    )
    ordenado_frequencia = sorted(
        [(n, st) for n, st in stats.items() if n in candidatas_saem],
        key=lambda it: (-it[1]['frequencia'], -it[1]['sequencia_atual'], it[0]),
    )

    entram = [n for n, _ in ordenado_atraso[:top_n]]
    saem: List[int] = []
    for n, _ in ordenado_frequencia:
        saem.append(n)
        if len(saem) >= top_n:
            break

    return sorted(entram), sorted(saem)


def compute_bola_da_vez_frequencia(
    hist_rows: Sequence[dict],
) -> List[Dict[str, int]]:
    """Build frequency table equivalent to notebook df_frequencia."""
    stats = _compute_bola_da_vez_stats(hist_rows)
    rows: List[Dict[str, int]] = []
    for numero in range(1, 26):
        st = stats[numero]
        rows.append({
            'numero': numero,
            'frequencia': st['frequencia'],
            'maiorSequencia': st['maior_sequencia'],
            'maiorAtraso': st['maior_atraso'],
            'sequenciaAtual': st['sequencia_atual'],
            'atrasoAtual': st['atraso_atual'],
        })

    rows.sort(key=lambda r: (-r['frequencia'], r['numero']))
    return rows


def filter_by_vector(list_values: Sequence[int], min_vec: Sequence[int], max_vec: Sequence[int]) -> bool:
    return all(min_vec[i] <= list_values[i] <= max_vec[i] for i in range(len(min_vec)))


def compute_freq_groups(freq_map: Dict[int, int]) -> Dict[str, set]:
    # Build percentage list and split into 4 quantile-like groups
    total = sum(freq_map.values()) or 1
    perc = {d: (freq_map[d] / total) * 100.0 for d in range(1, 26)}
    values = sorted(perc.values())
    # quartile thresholds
    t1 = values[int(len(values) * 1 / 4)]
    t2 = values[int(len(values) * 2 / 4)]
    t3 = values[int(len(values) * 3 / 4)]

    def classify(p: float) -> str:
        if p >= t3:
            return 'G1'
        elif p >= t2:
            return 'G2'
        elif p >= t1:
            return 'G3'
        else:
            return 'G4'

    groups = {'G1': set(), 'G2': set(), 'G3': set(), 'G4': set()}
    for d, p in perc.items():
        groups[classify(p)].add(d)
    return groups


def count_groups(dezenas: Sequence[int], groups: Dict[str, set]) -> Tuple[List[int], Dict[str, List[int]]]:
    s = set(dezenas)
    g1 = sorted(list(s & groups['G1']))
    g2 = sorted(list(s & groups['G2']))
    g3 = sorted(list(s & groups['G3']))
    g4 = sorted(list(s & groups['G4']))
    return [len(g1), len(g2), len(g3), len(g4)], {'G1': g1, 'G2': g2, 'G3': g3, 'G4': g4}


def compute_nah_sets(prev2: Sequence[int], prev1: Sequence[int]) -> Tuple[set, set, set]:
    # Given previous two draws, compute sets for last draw (prev1) relative to prev2
    s1 = set(prev1)
    s2 = set(prev2)
    N = s1 - s2
    A = (s1 & s2)
    H = s1 & s2  # not used here directly, A/H split depends on prev1 vs prev2 vs prev3 for last draw; for mapping, we use N_to_A and AH_to_H from last draw, we approximate as:
    return N, A, H


def compute_mapping_sets(current: Sequence[int], prev1: Sequence[int], prev2: Sequence[int]) -> Tuple[set, set, set]:
    # Mapping for bet classification relative to last draw:
    # NS_to_N: not in last draw (prev1)
    # N_to_A: numbers that were N in last draw (current vs prev1)
    # AH_to_H: numbers that were A or H in last draw (i.e., current∩prev1)
    s_cur = set(current)
    s_prev1 = set(prev1)
    s_prev2 = set(prev2)
    NS_to_N = set(range(1, 26)) - s_cur
    N_to_A = s_cur - s_prev1
    AH_to_H = s_cur & s_prev1  # A ∪ H for last draw
    return NS_to_N, N_to_A, AH_to_H


def generate_nah_variations(base: Tuple[int, int, int], var_range: int = 2) -> List[Tuple[int, int, int]]:
    bN, bA, bH = base
    combos = set()
    for dN in range(-var_range, var_range + 1):
        for dA in range(-var_range, var_range + 1):
            for dH in range(-var_range, var_range + 1):
                n, a, h = bN + dN, bA + dA, bH + dH
                if n < 0 or a < 0 or h < 0:
                    continue
                if n + a + h != 15:
                    continue
                combos.add((n, a, h))
    return sorted(list(combos))
