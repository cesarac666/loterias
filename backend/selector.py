from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple


def compute_number_frequencies(rows: Iterable[dict], last_n: int | None = None) -> Dict[int, int]:
    """Compute absolute frequency of each dezena (1..25) from historical result rows.

    rows: iterable of sqlite rows or dicts with keys n1..n15 in chronological order.
    last_n: if provided, only the last N rows are considered.
    """
    freqs = {i: 0 for i in range(1, 26)}
    rows_list = list(rows)
    if last_n is not None:
        rows_list = rows_list[-last_n:]
    for r in rows_list:
        for i in range(1, 16):
            d = r[f'n{i}']
            freqs[d] += 1
    return freqs


def jaccard_distance(a: Sequence[int], b: Sequence[int]) -> float:
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    union = len(sa | sb)
    if union == 0:
        return 0.0
    return 1.0 - inter / union


def _count_runs_of_consecutives(sorted_dezenas: Sequence[int]) -> int:
    """Count how many runs of length >= 3 exist in a sorted sequence."""
    runs = 0
    run_len = 1
    for i in range(1, len(sorted_dezenas)):
        if sorted_dezenas[i] == sorted_dezenas[i - 1] + 1:
            run_len += 1
        else:
            if run_len >= 3:
                runs += 1
            run_len = 1
    if run_len >= 3:
        runs += 1
    return runs


def _max_gap(sorted_dezenas: Sequence[int]) -> int:
    max_gap = 0
    for i in range(1, len(sorted_dezenas)):
        max_gap = max(max_gap, sorted_dezenas[i] - sorted_dezenas[i - 1])
    return max_gap


def score_bet(
    dezenas: Sequence[int],
    freq_map: Dict[int, int],
    *,
    w_freq: float = 1.0,
    w_seq3: float = -0.7,
    w_jump: float = -0.4,
    w_par_balance: float = -0.3,
) -> float:
    """Compute a simple heuristic score for a bet.

    - freq score: sum of historical frequencies for dezenas
    - seq3 penalty: penalize runs of 3+ consecutives
    - jump penalty: penalize large maximum gap (> 4)
    - par balance penalty: penalize deviation from balanced parity (7/8)
    """
    sdezenas = sorted(dezenas)
    freq_sum = sum(freq_map.get(d, 0) for d in dezenas)
    # normalize by an approximate scale: max freq per draw ~ 15, use sum of top-15 freqs as rough upper bound
    max_freq = max(freq_map.values()) or 1
    freq_norm = freq_sum / (15 * max_freq)

    runs3 = _count_runs_of_consecutives(sdezenas)
    jump = _max_gap(sdezenas)
    jump_pen = 1.0 if jump > 4 else 0.0

    pares = sum(1 for d in dezenas if d % 2 == 0)
    impares = 15 - pares
    # ideal is 7/8 or 8/7; deviation from 7.5
    par_dev = abs(pares - 7.5) / 7.5

    score = (
        w_freq * freq_norm
        + w_seq3 * runs3
        + w_jump * jump_pen
        + w_par_balance * par_dev
    )
    return float(score)


def select_diverse(
    candidates: List[Tuple[Sequence[int], float]],
    k: int,
    *,
    greedy_pool: int = 200,
) -> List[Tuple[Sequence[int], float]]:
    """Select up to k candidates balancing score and diversity using a two-phase approach.

    candidates: list of (dezenas, score)
    greedy_pool: consider only top-N by score for diversity selection
    """
    if not candidates:
        return []
    sorted_cand = sorted(candidates, key=lambda x: x[1], reverse=True)
    pool = sorted_cand[: max(greedy_pool, k)]
    selected: List[Tuple[Sequence[int], float]] = []
    # seed with best score
    selected.append(pool[0])
    while len(selected) < k and len(selected) < len(pool):
        best_idx = None
        best_dist = -1.0
        for idx in range(1, len(pool)):
            dezenas, sc = pool[idx]
            if any(dezenas is sel[0] for sel in selected):
                continue
            # compute min distance to current selected set
            mind = min(jaccard_distance(dezenas, sel[0]) for sel in selected)
            # maximize min distance; tie-break by score implicitly via ordering
            if mind > best_dist:
                best_dist = mind
                best_idx = idx
        if best_idx is None:
            break
        selected.append(pool[best_idx])
    return selected

