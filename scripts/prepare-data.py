import argparse
import re
from pathlib import Path

import pandas as pd


def base_headers():
    return [
        "psc_code",
        "psc_description",
        "contracting_dept_code",
        "contracting_dept_name",
        "contracting_agency_code",
        "contracting_agency_name",
        "funding_dept_code",
        "funding_dept_name",
        "funding_agency_code",
        "funding_agency_name",
        "pop_city",
        "pop_state",
        "pop_county",
        "pop_zip",
        "pop_country",
        "date_signed",
        "base_effective_date",
        "accepted_timestamp",
        "extent_competed",
        "fair_opportunity_limited_sources",
        "contract_type",
        "requirement_description",
        "additional_reporting",
        "inherently_gov_functions",
        "vendor_uei",
        "vendor_name",
        "vendor_cage_code",
        "referenced_idv_piid",
        "piid",
        "total_dollars_obligated",
        "total_base_all_options_value",
        "total_invoiced_amount",
        "total_hours_invoiced",
        "total_fte",
        "prime_hours_invoiced",
        "prime_fte",
    ]


def build_headers(max_subs: int = 100):
    base = list(base_headers())
    for i in range(1, max_subs + 1):
        base.extend(
            [
                f"sub{i}_contract_number",
                f"sub{i}_uei",
                f"sub{i}_name",
                f"sub{i}_hours_invoiced",
                f"sub{i}_fte",
            ]
        )
    return base


def drop_leading_blank_col(df):
    if df.shape[1] == 0:
        return df
    first_name = str(df.columns[0])
    if first_name.startswith("Unnamed") or df.iloc[:, 0].isna().all():
        return df.drop(columns=[df.columns[0]])
    return df


def detect_max_sub_index_from_names(columns):
    sub_re = re.compile(r"^sub(\d{1,3})_", re.IGNORECASE)
    indices = []
    for c in map(str, columns):
        m = sub_re.match(c)
        if m:
            try:
                indices.append(int(m.group(1)))
            except ValueError:
                pass
    return max(indices) if indices else 0


def align_headers(df, pad_subs):
    """Match df width to the header list (batch column adds).
    - If pad_subs is False, use detected subs (based on names or width).
    - If pad_subs is True, expand to 100 and add empty columns as needed.
    """

    detected_subs = detect_max_sub_index_from_names(df.columns)

    if detected_subs == 0:
        base_len = len(base_headers())
        if df.shape[1] >= base_len:
            detected_subs = max(0, (df.shape[1] - base_len) // 5)

    detected_subs = max(0, min(100, detected_subs))
    desired_subs = 100 if pad_subs else detected_subs

    headers = build_headers(desired_subs)
    target_cols = len(headers)
    current_cols = df.shape[1]

    if current_cols > target_cols:
        df = df.iloc[:, :target_cols]
    elif current_cols < target_cols:
        padding = target_cols - current_cols

        pad_cols = {
            f"_pad_{k}": pd.Series([""] * len(df), index=df.index)
            for k in range(padding)
        }
        df = pd.concat([df, pd.DataFrame(pad_cols, index=df.index)], axis=1)

        df = df.copy()

    df.columns = headers
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Service Contract Inventory Report for database import."
    )
    parser.add_argument("input", help="Path to the source file.")
    parser.add_argument("output", help="Path to the output file.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--csv", help="Convert the provied Excel file to CSV.", action="store_true"
    )
    group.add_argument(
        "--clean", help="Clean the provided CSV file.", action="store_true"
    )

    parser.add_argument(
        "--pad-subs",
        action="store_true",
        help="Pad subcontractor fields: append full sets beyond the highest present sub index up to 100.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if args.csv:
        df = pd.read_excel(input_path, header=3, dtype=str, engine="openpyxl")

        df = drop_leading_blank_col(df)

        try:
            df = align_headers(df, pad_subs=args.pad_subs)
        except Exception as e:
            print("ERROR: Column alignment error.")
            raise

        df.to_csv(output_path, index=False)

        print(f"Wrote: {output_path}")
        print(f"Rows: {len(df)}  |  Columns: {df.shape[1]}")
    elif args.clean:
        """ 
        Not 100% sure what is needed to clean the data yet, but as issues
        are discovered, this is where I'll address them.
        """

        print("Placeholder for future data cleaning, if needed.")
    else:
        print("No action.")


if __name__ == "__main__":
    main()
