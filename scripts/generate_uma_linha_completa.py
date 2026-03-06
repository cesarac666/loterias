from __future__ import annotations

import argparse
import csv
import itertools
import time
from pathlib import Path


def generate_uma_linha_completa(output_csv: Path) -> int:
    """Generate all Lotofacil bets with at least one complete line (5 numbers in a row)."""
    linhas = [
        tuple(range(1, 6)),
        tuple(range(6, 11)),
        tuple(range(11, 16)),
        tuple(range(16, 21)),
        tuple(range(21, 26)),
    ]

    combos = {}
    for idx, linha in enumerate(linhas):
        for k in range(6):
            combos[(idx, k)] = list(itertools.combinations(linha, k))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    header = [f"B{i}" for i in range(1, 16)]
    total = 0
    started_at = time.time()

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for sizes in itertools.product(range(6), repeat=5):
            if sum(sizes) != 15:
                continue
            if 5 not in sizes:
                continue

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
    default_output = Path(__file__).resolve().parent.parent / "todasUmaLinhaCompleta.csv"
    parser = argparse.ArgumentParser(
        description="Generate all Lotofacil combinations classified as '1 linha completa'."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output CSV path (default: {default_output})",
    )
    args = parser.parse_args()

    total = generate_uma_linha_completa(args.output)
    print(f"[done] arquivo: {args.output}")
    print(f"[done] total de apostas: {total:,}")


if __name__ == "__main__":
    main()

