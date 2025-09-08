import argparse
import re
from pathlib import Path

import pandas as pd

SUB_FIELDS = ["contract_number", "uei", "name", "hours_invoiced", "fte"]
SUB_REGEX = re.compile(
    r"^sub(\d+)_(contract_number|uei|name|hours_invoiced|fte)$")


def process_chunk(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace({"": pd.NA, " ": pd.NA})

    sub_cols = [c for c in df.columns if SUB_REGEX.match(c)]
    if not sub_cols:
        return pd.DataFrame(
            columns=["referenced_idv_piid", "piid",
                     "composite_key", "sub_index"]
            + SUB_FIELDS
        )

    pairs = []
    for c in sub_cols:
        m = SUB_REGEX.match(c)
        pairs.append((int(m.group(1)), m.group(2)))
    sub_df = df[sub_cols].copy()
    sub_df.columns = pd.MultiIndex.from_tuples(
        pairs, names=["sub_index", "field"])

    long = sub_df.stack(level=0, future_stack=True)
    long = long.reset_index(level=1).rename(columns={"level_1": "sub_index"})

    for f in SUB_FIELDS:
        if f not in long.columns:
            long[f] = pd.NA

    carriers = df[["referenced_idv_piid", "piid", "composite_key"]].copy()
    carriers = carriers.loc[long.index]
    out = pd.concat(
        [carriers.reset_index(drop=True), long.reset_index(drop=True)], axis=1
    )

    mask_any = out[SUB_FIELDS].notna().any(axis=1)
    out = out[mask_any].copy()

    for col in [
        "referenced_idv_piid",
        "piid",
        "composite_key",
        "sub_index",
    ] + SUB_FIELDS:
        if col in out.columns:
            out[col] = out[col].astype("string")

    return out[
        ["referenced_idv_piid", "piid", "composite_key", "sub_index"] + SUB_FIELDS
    ]


def main():
    ap = argparse.ArgumentParser(
        description="Process the wide CSV into rows for each subcontractor"
    )
    ap.add_argument("input", help="Source CSV")
    ap.add_argument("output", help="Destination CSV")
    ap.add_argument("--chunksize", type=int,
                    default=200_000, help="Rows per chunk")
    args = ap.parse_args()

    src = Path(args.input)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)

    def usecols(c):
        return c.startswith("sub") or c in (
            "referenced_idv_piid",
            "piid",
            "composite_key",
        )

    first = True
    for chunk in pd.read_csv(src, dtype=str, usecols=usecols, chunksize=args.chunksize):
        out_chunk = process_chunk(chunk)
        if first:
            out_chunk.to_csv(dest, index=False, mode="w")
            first = False
        else:
            out_chunk.to_csv(dest, index=False, mode="a", header=False)


if __name__ == "__main__":
    main()
