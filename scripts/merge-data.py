import argparse
import csv
import glob
import os
import sys


def read_header(csv_path, encoding):
    with open(csv_path, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            return []


def headers_match(a, b):
    return [h.strip() for h in a] == [h.strip() for h in b]


def merge_csvs(input_dir, pattern, output_path, col_name, encoding, recursive):
    search_glob = os.path.join(input_dir, pattern)
    files = sorted(glob.glob(search_glob, recursive=recursive))
    if not files:
        print(f"No files matched {search_glob}", file=sys.stderr)
        sys.exit(2)

    ref_header = None
    header_source = None
    nonempty_files = []

    for fp in files:
        hdr = read_header(fp, encoding)
        if hdr:
            if ref_header is None:
                ref_header = hdr
                header_source = fp
            nonempty_files.append(fp)

    if ref_header is None:
        print("All matched CSVs are empty; nothing to merge.", file=sys.stderr)
        sys.exit(3)

    out_header = [col_name] + ref_header

    written_rows = 0
    with open(output_path, "w", encoding=encoding, newline="") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(out_header)

        for fp in nonempty_files:
            hdr = read_header(fp, encoding)
            if not headers_match(hdr, ref_header):
                print(
                    f"Header mismatch in {fp}\n"
                    f"  Expected (from {header_source}): {ref_header}\n"
                    f"  Found: {hdr}",
                    file=sys.stderr,
                )
                sys.exit(4)

            with open(fp, "r", encoding=encoding, newline="") as in_f:
                reader = csv.DictReader(in_f)
                base = os.path.basename(fp)
                prefix = base[:4]
                for row in reader:
                    data_row = [prefix] + \
                        [row.get(col, "") for col in ref_header]
                    writer.writerow(data_row)
                    written_rows += 1

    print(
        f"Merged {len(nonempty_files)} file(s) with header from '{os.path.basename(header_source)}' "
        f"into '{output_path}' ({written_rows} rows)."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Merge CSV files with identical headers, adding a first column "
                    "with the first four characters of each source filename."
    )
    parser.add_argument(
        "input_dir", help="Directory containing CSV files to merge.")
    parser.add_argument("output", help="Path to the merged output CSV.")
    parser.add_argument("--pattern", default="*.csv",
                        help="Glob pattern for input files (default: *.csv).")
    parser.add_argument("--col-name", default="file_id",
                        help="Name of the new first column (default: file_id).")
    parser.add_argument("--encoding", default="utf-8-sig",
                        help="File encoding for input/output (default: utf-8-sig).")
    parser.add_argument("--recursive", action="store_true",
                        help="If set, search nested folders too.")
    args = parser.parse_args()

    merge_csvs(
        input_dir=args.input_dir,
        pattern=args.pattern,
        output_path=args.output,
        col_name=args.col_name,
        encoding=args.encoding,
        recursive=args.recursive,
    )


if __name__ == "__main__":
    main()
