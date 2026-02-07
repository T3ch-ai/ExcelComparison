"""
Workbook Builder: Assembles the final output Excel workbook.
  - Summary dashboard
  - Comparison_Results (with clickable hyperlinks to drill-down sheets)
  - QES_Network_Adequacy, QES_Providers, NIQ_Network_Adequacy, NIQ_Providers
  - Drill-down sub-sheets per County x Specialty
All labels are plain ASCII from config.
"""

import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows


def build_output_workbook(
    qes_na: pd.DataFrame,
    qes_providers: pd.DataFrame,
    niq_na: pd.DataFrame,
    niq_providers: pd.DataFrame,
    comparison: pd.DataFrame,
    cfg: dict,
) -> str:
    out_cfg = cfg["output"]
    colors = out_cfg.get("colors", {})
    labels = out_cfg["labels"]

    wb = Workbook()
    wb.remove(wb.active)

    styles = _build_styles(colors)

    # --- 1. Create drill-down sub-sheets ---
    key_qes = cfg["key_columns"]["qes"]
    key_niq = cfg["key_columns"]["niq"]
    max_dd = out_cfg.get("max_drilldown_sheets", 200)
    county_col = key_qes[1]
    spec_col = key_qes[2]

    combos = []
    for _, row in comparison.iterrows():
        combo = (row.get(county_col, ""), row.get(spec_col, ""))
        if combo not in combos:
            combos.append(combo)

    qes_dd_index = {}
    niq_dd_index = {}
    dd_count = 0
    all_dd_names = []

    for county, specialty in combos:
        if dd_count >= max_dd:
            break

        # QES drill-down
        qes_filtered = _filter_providers(qes_providers, key_qes[1], county, key_qes[2], specialty)
        if len(qes_filtered) > 0:
            sname = _safe_sheet_name(f"QES_{county}_{specialty}", all_dd_names)
            all_dd_names.append(sname)
            ws = wb.create_sheet(title=sname)
            _write_drilldown_sheet(ws, qes_filtered, county, specialty, "QES", styles, out_cfg)
            qes_dd_index[(county, specialty)] = sname
            dd_count += 1

        # NIQ drill-down
        niq_filtered = _filter_providers(niq_providers, key_niq[1], county, key_niq[2], specialty)
        if len(niq_filtered) > 0:
            sname = _safe_sheet_name(f"NIQ_{county}_{specialty}", all_dd_names)
            all_dd_names.append(sname)
            ws = wb.create_sheet(title=sname)
            _write_drilldown_sheet(ws, niq_filtered, county, specialty, "NIQ", styles, out_cfg)
            niq_dd_index[(county, specialty)] = sname
            dd_count += 1

    print(f"  [built] {dd_count} drill-down sheets")

    # --- 2. Comparison Results ---
    ws_comp = wb.create_sheet(title="Comparison_Results", index=0)
    _write_comparison_sheet(ws_comp, comparison, cfg, qes_dd_index, niq_dd_index, styles, labels, out_cfg)

    # --- 3. Summary ---
    ws_summ = wb.create_sheet(title="Summary", index=0)
    _write_summary_sheet(ws_summ, comparison, cfg, styles, labels)

    # --- 4. Raw data sheets ---
    for title, df in [
        ("QES_Network_Adequacy", qes_na),
        ("QES_Providers", qes_providers),
        ("NIQ_Network_Adequacy", niq_na),
        ("NIQ_Providers", niq_providers),
    ]:
        ws = wb.create_sheet(title=title)
        _write_data_sheet(ws, df, styles, out_cfg)

    # --- Save ---
    os.makedirs(os.path.dirname(out_cfg["workbook_path"]) or ".", exist_ok=True)
    wb.save(out_cfg["workbook_path"])
    print(f"\n  [saved] {out_cfg['workbook_path']} ({len(wb.sheetnames)} sheets)")
    return out_cfg["workbook_path"]


# ============================================================================
# Styles
# ============================================================================

def _build_styles(colors: dict) -> dict:
    return {
        "header_fill": PatternFill("solid", fgColor=colors.get("header_fill", "1F4E79")),
        "header_font": Font(name="Arial", bold=True, color=colors.get("header_font", "FFFFFF"), size=10),
        "data_font": Font(name="Arial", size=10),
        "match_fill": PatternFill("solid", fgColor=colors.get("match_fill", "C6EFCE")),
        "mismatch_fill": PatternFill("solid", fgColor=colors.get("mismatch_fill", "FFC7CE")),
        "qes_only_fill": PatternFill("solid", fgColor=colors.get("qes_only_fill", "FCE4D6")),
        "niq_only_fill": PatternFill("solid", fgColor=colors.get("niq_only_fill", "D6E4FC")),
        "hyperlink_font": Font(name="Arial", size=10, underline="single",
                               color=colors.get("hyperlink_font", "0563C1")),
        "border": Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        ),
        "title_font": Font(name="Arial", bold=True, size=14, color="1F4E79"),
        "subtitle_font": Font(name="Arial", bold=True, size=11, color="1F4E79"),
        "metric_font": Font(name="Arial", size=11),
        "big_number_font": Font(name="Arial", bold=True, size=16, color="1F4E79"),
        "bold_font": Font(name="Arial", bold=True, size=11),
    }


# ============================================================================
# Sheet Writers
# ============================================================================

def _write_data_sheet(ws, df, styles, out_cfg):
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.border = styles["border"]
            if r_idx == 1:
                cell.fill = styles["header_fill"]
                cell.font = styles["header_font"]
                cell.alignment = Alignment(horizontal="center", wrap_text=True)
            else:
                cell.font = styles["data_font"]
    if out_cfg.get("freeze_panes"):
        ws.freeze_panes = "A2"
    if out_cfg.get("auto_column_width"):
        _auto_width(ws)


def _write_comparison_sheet(ws, comparison, cfg, qes_dd_index, niq_dd_index, styles, labels, out_cfg):
    compare_cols = cfg["compare_columns"]
    drilldown_cfg = cfg["drilldown"]
    key_qes = cfg["key_columns"]["qes"]
    county_col = key_qes[1]
    spec_col = key_qes[2]

    # Identify which result columns are drilldown-linked
    dd_qes_result_col = None
    dd_niq_result_col = None
    for cc in compare_cols:
        if cc["qes_col"] == drilldown_cfg["qes_column"]:
            dd_qes_result_col = f"QES_{cc['label']}"
        if cc["niq_col"] == drilldown_cfg["niq_column"]:
            dd_niq_result_col = f"NIQ_{cc['label']}"

    columns = list(comparison.columns)

    # Header
    for c_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=c_idx, value=col_name)
        cell.fill = styles["header_fill"]
        cell.font = styles["header_font"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = styles["border"]

    # Data rows
    for r_idx, (_, data_row) in enumerate(comparison.iterrows(), 2):
        county = data_row.get(county_col, "")
        specialty = data_row.get(spec_col, "")
        row_source = data_row.get("Row_Source", "Both")

        for c_idx, col_name in enumerate(columns, 1):
            value = data_row[col_name]
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = styles["border"]
            cell.font = styles["data_font"]

            # Hyperlink: QES drilldown
            if col_name == dd_qes_result_col and (county, specialty) in qes_dd_index:
                cell.value = value
                cell.hyperlink = f"#'{qes_dd_index[(county, specialty)]}'!A1"
                cell.font = styles["hyperlink_font"]
                continue

            # Hyperlink: NIQ drilldown
            if col_name == dd_niq_result_col and (county, specialty) in niq_dd_index:
                cell.value = value
                cell.hyperlink = f"#'{niq_dd_index[(county, specialty)]}'!A1"
                cell.font = styles["hyperlink_font"]
                continue

            cell.value = "" if pd.isna(value) else value

            # Conditional coloring
            if col_name.startswith("Match_") or col_name == "Overall_Match":
                str_val = str(value)
                if str_val == labels["match"] or str_val == labels["overall_match"]:
                    cell.fill = styles["match_fill"]
                elif str_val == labels["mismatch"] or str_val == labels["overall_mismatch"]:
                    cell.fill = styles["mismatch_fill"]
                elif str_val == labels["warning"]:
                    if row_source == "QES Only":
                        cell.fill = styles["qes_only_fill"]
                    else:
                        cell.fill = styles["niq_only_fill"]
                elif str_val in (labels["overall_qes_only"], labels["overall_niq_only"]):
                    cell.fill = styles["qes_only_fill"] if "QES" in str_val else styles["niq_only_fill"]

    if out_cfg.get("freeze_panes"):
        ws.freeze_panes = "A2"
    if out_cfg.get("auto_column_width"):
        _auto_width(ws)
    ws.auto_filter.ref = ws.dimensions


def _write_drilldown_sheet(ws, df, county, specialty, source_label, styles, out_cfg):
    title = f"{source_label} Providers -- {county} / {specialty}"
    ws.cell(row=1, column=1, value=title).font = styles["title_font"]
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=min(len(df.columns), 9))

    back_cell = ws.cell(row=2, column=1, value="<< Back to Comparison Results")
    back_cell.hyperlink = "#Comparison_Results!A1"
    back_cell.font = styles["hyperlink_font"]

    start_row = 4
    for c_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=start_row, column=c_idx, value=col_name)
        cell.fill = styles["header_fill"]
        cell.font = styles["header_font"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = styles["border"]

    for r_idx, (_, data_row) in enumerate(df.iterrows(), start_row + 1):
        for c_idx, col_name in enumerate(df.columns, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=data_row[col_name])
            cell.font = styles["data_font"]
            cell.border = styles["border"]

    if out_cfg.get("freeze_panes"):
        ws.freeze_panes = f"A{start_row + 1}"
    if out_cfg.get("auto_column_width"):
        _auto_width(ws)


def _write_summary_sheet(ws, comparison, cfg, styles, labels):
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 35
    ws.column_dimensions["C"].width = 18

    r = 2
    ws.cell(row=r, column=2, value="Network Adequacy Comparison Report").font = styles["title_font"]
    r += 1
    ws.cell(row=r, column=2, value=f"State: {cfg['state']}").font = styles["subtitle_font"]
    r += 1
    ws.cell(row=r, column=2, value=f"NIQ Source: {cfg['niq']['source_type']}").font = styles["metric_font"]
    r += 2

    total = len(comparison)
    both = len(comparison[comparison["Row_Source"] == "Both"])
    matches = len(comparison[comparison["Overall_Match"] == labels["overall_match"]])
    mismatches = len(comparison[comparison["Overall_Match"] == labels["overall_mismatch"]])
    qes_only = len(comparison[comparison["Row_Source"] == "QES Only"])
    niq_only = len(comparison[comparison["Row_Source"] == "NIQ Only"])
    match_pct = f"{matches/both*100:.1f}%" if both > 0 else "N/A"

    ws.cell(row=r, column=2, value="Overall Metrics").font = styles["subtitle_font"]
    r += 1
    metrics = [
        ("Total County x Specialty Combinations", total),
        ("Present in Both Systems", both),
        ("Fully Matching", matches),
        ("With Differences", mismatches),
        ("In QES Only (not in NIQ)", qes_only),
        ("In NIQ Only (not in QES)", niq_only),
        ("Match Rate", match_pct),
    ]
    for label_text, val in metrics:
        ws.cell(row=r, column=2, value=label_text).font = styles["metric_font"]
        c = ws.cell(row=r, column=3, value=val)
        c.font = styles["big_number_font"] if label_text == "Match Rate" else styles["bold_font"]
        c.alignment = Alignment(horizontal="center")
        r += 1

    r += 1
    ws.cell(row=r, column=2, value="Mismatches by Column").font = styles["subtitle_font"]
    r += 1
    for cc in cfg["compare_columns"]:
        match_col = f"Match_{cc['label']}"
        if match_col in comparison.columns:
            mm_count = len(comparison[comparison[match_col] == labels["mismatch"]])
            ws.cell(row=r, column=2, value=cc["label"]).font = styles["metric_font"]
            ws.cell(row=r, column=3, value=mm_count).font = styles["bold_font"]
            r += 1

    r += 1
    link_cell = ws.cell(row=r, column=2, value=">> View Full Comparison Details")
    link_cell.hyperlink = "#Comparison_Results!A1"
    link_cell.font = styles["hyperlink_font"]


# ============================================================================
# Utilities
# ============================================================================

def _safe_sheet_name(name: str, existing: list, max_len: int = 31) -> str:
    for ch in ['\\', '/', '*', '?', ':', '[', ']']:
        name = name.replace(ch, "_")
    name = name[:max_len]
    original = name
    counter = 1
    while name in existing:
        suffix = f"_{counter}"
        name = original[:max_len - len(suffix)] + suffix
        counter += 1
    return name


def _filter_providers(df, county_col, county, spec_col, specialty):
    mask = (df[county_col].astype(str) == str(county)) & (df[spec_col].astype(str) == str(specialty))
    return df[mask].reset_index(drop=True)


def _auto_width(ws, min_width=10, max_width=40):
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, min_width), max_width)
