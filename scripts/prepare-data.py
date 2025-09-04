import argparse
import sys
from pathlib import Path

import pandas as pd


def build_headers():
    base = [
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
    for i in range(1, 101):
        base.extend(
            [
                f"sub{i}_contract_number",
                f"sub{i}_uei",
                f"sub{i}_name",
                f"sub{i}_hours_invoiced",
                f"sub{i}_fte",
            ]
        )
    return base  # 536 total


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

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if args.csv:
        df = pd.read_excel(input_path, header=3, dtype=str, engine="openpyxl")

        if df.shape[1] > 0:
            first_col = str(df.columns[0])
            if first_col.startswith("Unnamed") or (df.iloc[:, 0].isna().all()):
                df = df.drop(columns=[df.columns[0]])

        headers = build_headers()

        target_cols = len(headers)
        current_cols = df.shape[1]

        if current_cols != target_cols:
            print("ERROR: Column count mis-match.")
            sys.exit(1)

        df.columns = headers

        df.to_csv(output_path, index=False)

        print(f"Wrote: {output_path}")
        print(f"Rows: {len(df)}  |  Columns: {df.shape[1]} (expected {target_cols})")
    elif args.clean:
        """ 
        Not 100% what is needed to clean the data, but as issues
        are discovered, this is where I'll address them.
        """

        print("Placeholder for future data cleaning, if needed.")
    else:
        print("No action.")


if __name__ == "__main__":
    main()
