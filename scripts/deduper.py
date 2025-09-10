import argparse
import csv
import hashlib
import json
from pathlib import Path


def row_checksum(values):
    s = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def process(input_path: Path, output_path: Path, dedup: bool) -> int:
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return 2

    with (
        input_path.open("r", newline="", encoding="utf-8") as f_in,
        output_path.open("w", newline="", encoding="utf-8") as f_out,
    ):
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)

        header = next(reader, None)
        if header is None:
            print("ERROR: Input CSV appears to be empty (no header).")
            return 3

        writer.writerow(["checksum"] + header)

        seen = set()
        total_rows = 0
        duplicate_rows = 0
        written_rows = 0

        for row in reader:
            total_rows += 1

            checksum = row_checksum(row)
            is_duplicate = checksum in seen

            if is_duplicate:
                duplicate_rows += 1
            else:
                seen.add(checksum)

            if dedup and is_duplicate:
                continue

            writer.writerow([checksum] + row)
            written_rows += 1

        unique_rows = len(seen)
        print(f"Rows processed: {total_rows}")
        print(f"Unique rows: {unique_rows}")
        print(f"Duplicates found: {duplicate_rows}")
        if dedup:
            print(f"Rows written after dedup: {written_rows}")
        else:
            print(f"Rows written: {written_rows}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Add a row checksum column to a CSV and optionally deduplicate by checksum."
    )
    parser.add_argument("input", help="Path to the input CSV")
    parser.add_argument("output", help="Path to the output CSV")
    parser.add_argument(
        "--dedup",
        action="store_true",
        help="If set, write only one row per unique checksum",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    code = process(input_path, output_path, dedup=args.dedup)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
