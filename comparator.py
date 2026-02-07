"""
Comparator: Joins QES and NIQ on configurable keys, compares configurable columns,
includes additional display-only columns, and respects configurable result column order.
All flag labels are plain ASCII from config.
"""

import pandas as pd
import numpy as np


def compare_network_adequacy(
    qes_na: pd.DataFrame,
    niq_na: pd.DataFrame,
    cfg: dict,
) -> pd.DataFrame:
    key_qes = cfg["key_columns"]["qes"]
    key_niq = cfg["key_columns"]["niq"]
    compare_cols = cfg["compare_columns"]
    additional_cols = cfg.get("additional_result_columns", [])
    labels = cfg["output"]["labels"]

    join_key = "_join_key"
    qes_work = qes_na.copy()
    niq_work = niq_na.copy()
    qes_work[join_key] = qes_work[key_qes].astype(str).agg("|".join, axis=1)
    niq_work[join_key] = niq_work[key_niq].astype(str).agg("|".join, axis=1)

    all_qes_keys = set(qes_work[join_key])
    all_niq_keys = set(niq_work[join_key])
    both_keys = all_qes_keys & all_niq_keys
    qes_only_keys = all_qes_keys - all_niq_keys
    niq_only_keys = all_niq_keys - all_qes_keys

    qes_idx = qes_work.set_index(join_key)
    niq_idx = niq_work.set_index(join_key)

    results = []

    # --- Both ---
    for jk in sorted(both_keys):
        qr = qes_idx.loc[jk]
        nr = niq_idx.loc[jk]
        if isinstance(qr, pd.DataFrame):
            qr = qr.iloc[0]
        if isinstance(nr, pd.DataFrame):
            nr = nr.iloc[0]

        row = {"Row_Source": "Both"}
        for kc in key_qes:
            row[kc] = qr[kc]

        any_mismatch = False
        for cc in compare_cols:
            qval = qr.get(cc["qes_col"])
            nval = nr.get(cc["niq_col"])
            lbl = cc["label"]
            dtype = cc.get("dtype", "text")
            tol = cc.get("tolerance", 0)

            row[f"QES_{lbl}"] = qval
            row[f"NIQ_{lbl}"] = nval
            match, diff = _compare_values(qval, nval, dtype, tol, labels)
            row[f"Diff_{lbl}"] = diff
            row[f"Match_{lbl}"] = labels["match"] if match else labels["mismatch"]
            if not match:
                any_mismatch = True

        for ac in additional_cols:
            lbl = ac["label"]
            row[f"QES_{lbl}"] = qr.get(ac["qes_col"]) if ac.get("qes_col") else None
            row[f"NIQ_{lbl}"] = nr.get(ac["niq_col"]) if ac.get("niq_col") else None

        row["Overall_Match"] = labels["overall_mismatch"] if any_mismatch else labels["overall_match"]
        results.append(row)

    # --- QES Only ---
    for jk in sorted(qes_only_keys):
        qr = qes_idx.loc[jk]
        if isinstance(qr, pd.DataFrame):
            qr = qr.iloc[0]

        row = {"Row_Source": "QES Only"}
        for kc in key_qes:
            row[kc] = qr[kc]
        for cc in compare_cols:
            lbl = cc["label"]
            row[f"QES_{lbl}"] = qr.get(cc["qes_col"])
            row[f"NIQ_{lbl}"] = None
            row[f"Diff_{lbl}"] = labels["na_qes_only"]
            row[f"Match_{lbl}"] = labels["warning"]
        for ac in additional_cols:
            lbl = ac["label"]
            row[f"QES_{lbl}"] = qr.get(ac["qes_col"]) if ac.get("qes_col") else None
            row[f"NIQ_{lbl}"] = None
        row["Overall_Match"] = labels["overall_qes_only"]
        results.append(row)

    # --- NIQ Only ---
    for jk in sorted(niq_only_keys):
        nr = niq_idx.loc[jk]
        if isinstance(nr, pd.DataFrame):
            nr = nr.iloc[0]

        row = {"Row_Source": "NIQ Only"}
        for i, kc in enumerate(key_qes):
            row[kc] = nr[key_niq[i]]
        for cc in compare_cols:
            lbl = cc["label"]
            row[f"QES_{lbl}"] = None
            row[f"NIQ_{lbl}"] = nr.get(cc["niq_col"])
            row[f"Diff_{lbl}"] = labels["na_niq_only"]
            row[f"Match_{lbl}"] = labels["warning"]
        for ac in additional_cols:
            lbl = ac["label"]
            row[f"QES_{lbl}"] = None
            row[f"NIQ_{lbl}"] = nr.get(ac["niq_col"]) if ac.get("niq_col") else None
        row["Overall_Match"] = labels["overall_niq_only"]
        results.append(row)

    result_df = pd.DataFrame(results)
    result_df = _apply_column_order(result_df, cfg)

    _print_summary(result_df, labels)
    return result_df


def _compare_values(qes_val, niq_val, dtype, tolerance, labels):
    if pd.isna(qes_val) and pd.isna(niq_val):
        return True, 0
    if pd.isna(qes_val) or pd.isna(niq_val):
        return False, labels["null_vs_value"]
    if dtype == "numeric":
        try:
            q, n = float(qes_val), float(niq_val)
            diff = round(n - q, 6)
            return abs(diff) <= tolerance, diff
        except (ValueError, TypeError):
            return str(qes_val) == str(niq_val), f"{qes_val} vs {niq_val}"
    match = str(qes_val).strip().upper() == str(niq_val).strip().upper()
    diff = "" if match else f"{qes_val} -> {niq_val}"
    return match, diff


def _apply_column_order(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Reorder columns based on result_column_order config tokens."""
    order_cfg = cfg.get("result_column_order")
    if not order_cfg:
        return df

    key_qes = cfg["key_columns"]["qes"]
    compare_cols = cfg["compare_columns"]
    additional_cols = cfg.get("additional_result_columns", [])

    ordered = []
    for token in order_cfg:
        token = token.strip()
        if token == "{keys}":
            ordered.extend(key_qes)
        elif token == "{row_source}":
            ordered.append("Row_Source")
        elif token == "{overall_match}":
            ordered.append("Overall_Match")
        elif token.startswith("{compare:") and token.endswith("}"):
            lbl = token[len("{compare:"):-1]
            ordered.extend([f"QES_{lbl}", f"NIQ_{lbl}", f"Diff_{lbl}", f"Match_{lbl}"])
        elif token.startswith("{additional:") and token.endswith("}"):
            lbl = token[len("{additional:"):-1]
            ordered.extend([f"QES_{lbl}", f"NIQ_{lbl}"])
        else:
            ordered.append(token)

    # Only keep columns that exist in the dataframe
    ordered = [c for c in ordered if c in df.columns]
    # Append any remaining columns not in the order (safety net)
    remaining = [c for c in df.columns if c not in ordered]
    return df[ordered + remaining]


def _print_summary(result_df, labels):
    total = len(result_df)
    both = len(result_df[result_df["Row_Source"] == "Both"])
    matches = len(result_df[result_df["Overall_Match"] == labels["overall_match"]])
    mismatches = len(result_df[result_df["Overall_Match"] == labels["overall_mismatch"]])
    qes_only = len(result_df[result_df["Row_Source"] == "QES Only"])
    niq_only = len(result_df[result_df["Row_Source"] == "NIQ Only"])

    print(f"\n  Comparison Summary:")
    print(f"     Total rows examined : {total}")
    if both > 0:
        print(f"     Matched             : {matches}/{both} ({matches/both*100:.1f}%)")
        print(f"     Mismatched          : {mismatches}/{both}")
    else:
        print(f"     Matched             : 0")
        print(f"     Mismatched          : 0")
    print(f"     QES Only            : {qes_only}")
    print(f"     NIQ Only            : {niq_only}")
