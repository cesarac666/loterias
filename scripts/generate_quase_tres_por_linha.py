from __future__ import annotations

import argparse
import csv
import itertools
import time
from pathlib import Path


def generate_quase_tres_por_linha(output_csv: Path) -> int:
    """Generate all Lotofacil bets with line profile 3,3,3,2,4 (any line order)."""
    linhas = [
        tuple(range(1, 6)),
        tuple(range(6, 11)),
        tuple(range(11, 16)),
        tuple(range(16, 21)),
        tuple(range(21, 26)),
    ]

    combos = {}
    for idx, linha in enumerate(linhas):
        for k in (2, 3, 4):
            combos[(idx, k)] = list(itertools.combinations(linha, k))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    header = [f"B{i}" for i in range(1, 16)]
    total = 0
    started_at = time.time()

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for linha_com_2 in range(5):
            for linha_com_4 in range(5):
                if linha_com_4 == linha_com_2:
                    continue

                sizes = [3, 3, 3, 3, 3]
                sizes[linha_com_2] = 2
                sizes[linha_com_4] = 4

                iterables = [combos[(idx, sizes[idx])] for idx in range(5)]
                for parts in itertools.product(*iterables):
                    bet = list(itertools.chain.from_iterable(parts))
                    writer.writerow(bet)
                    total += 1

                    if total % 100_000 == 0:
                        elapsed = time.time() - started_at
                        print(f"[progress] {total:,} linhas em {elapsed:.1f}s")

    return total


def main() -> None:
    default_output = Path(__file__).resolve().parent.parent / "todasQuaseTresPorLinha.csv"
    parser = argparse.ArgumentParser(
        description="Generate all Lotofacil combinations classified as 'quase 3 por linha'."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output CSV path (default: {default_output})",
    )
    args = parser.parse_args()

    total = generate_quase_tres_por_linha(args.output)
    print(f"[done] arquivo: {args.output}")
    print(f"[done] total de apostas: {total:,}")


if __name__ == "__main__":
    main()

