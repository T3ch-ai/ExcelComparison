"""
Data loader: Loads QES from Excel workbooks, NIQ from Excel / RDS / CSV / mock.
All column names come from config.
"""

import pandas as pd
from config_loader import get_rds_connection_string


def load_qes_data(cfg: dict) -> tuple:
    """Load QES-set-1 (Network Adequacy) and QES-set-2 (Providers) from Excel."""
    qes = cfg["qes"]
    state = cfg["state"]
    state_col = cfg["key_columns"]["qes"][0]

    qes_na = pd.read_excel(qes["workbook1_path"], sheet_name=qes.get("workbook1_sheet", 0))
    qes_provs = pd.read_excel(qes["workbook2_path"], sheet_name=qes.get("workbook2_sheet", 0))

    qes_na = qes_na[qes_na[state_col] == state].reset_index(drop=True)
    qes_provs = qes_provs[qes_provs[state_col] == state].reset_index(drop=True)

    print(f"  [loaded] QES-set-1: {len(qes_na)} rows from {qes['workbook1_path']}")
    print(f"  [loaded] QES-set-2: {len(qes_provs)} rows from {qes['workbook2_path']}")
    return qes_na, qes_provs


def load_niq_data(cfg: dict) -> tuple:
    """Load NIQ data based on configured source_type."""
    src = cfg["niq"]["source_type"]
    loaders = {
        "excel": _load_niq_excel,
        "rds": _load_niq_rds,
        "csv": _load_niq_csv,
        "mock": _load_niq_mock,
    }
    if src not in loaders:
        raise ValueError(f"Unknown niq.source_type: {src}")
    return loaders[src](cfg)


def _load_niq_excel(cfg: dict) -> tuple:
    """Load NIQ from Excel workbook(s). Supports single workbook with two sheets
    or two separate workbooks -- controlled by config."""
    excel_cfg = cfg["niq"]["excel"]
    state = cfg["state"]
    state_col = cfg["key_columns"]["niq"][0]

    single = excel_cfg.get("single_workbook", True)

    if single:
        wb_path = excel_cfg["workbook_path"]
        na_sheet = excel_cfg.get("network_adequacy_sheet", 0)
        prov_sheet = excel_cfg.get("provider_detail_sheet", 1)
        niq_na = pd.read_excel(wb_path, sheet_name=na_sheet)
        niq_provs = pd.read_excel(wb_path, sheet_name=prov_sheet)
        src_label = f"{wb_path} [{na_sheet}, {prov_sheet}]"
    else:
        wb1 = excel_cfg["workbook1_path"]
        wb2 = excel_cfg["workbook2_path"]
        niq_na = pd.read_excel(wb1, sheet_name=excel_cfg.get("workbook1_sheet", 0))
        niq_provs = pd.read_excel(wb2, sheet_name=excel_cfg.get("workbook2_sheet", 0))
        src_label = f"{wb1} + {wb2}"

    niq_na = niq_na[niq_na[state_col] == state].reset_index(drop=True)
    niq_provs = niq_provs[niq_provs[state_col] == state].reset_index(drop=True)

    print(f"  [loaded] NIQ-set-1: {len(niq_na)} rows from {src_label}")
    print(f"  [loaded] NIQ-set-2: {len(niq_provs)} rows from {src_label}")
    return niq_na, niq_provs


def _load_niq_rds(cfg: dict) -> tuple:
    from sqlalchemy import create_engine, text

    conn_str = get_rds_connection_string(cfg)
    engine = create_engine(conn_str)
    rds_cfg = cfg["niq"]["rds"]
    state = cfg["state"]

    with engine.connect() as conn:
        niq_na = pd.read_sql(text(rds_cfg["network_adequacy_query"]), conn, params={"state": state})
        niq_provs = pd.read_sql(text(rds_cfg["provider_detail_query"]), conn, params={"state": state})

    print(f"  [loaded] NIQ-set-1: {len(niq_na)} rows from RDS")
    print(f"  [loaded] NIQ-set-2: {len(niq_provs)} rows from RDS")
    return niq_na, niq_provs


def _load_niq_csv(cfg: dict) -> tuple:
    csv_cfg = cfg["niq"]["csv"]
    state = cfg["state"]
    state_col = cfg["key_columns"]["niq"][0]

    niq_na = pd.read_csv(csv_cfg["network_adequacy_path"])
    niq_provs = pd.read_csv(csv_cfg["provider_detail_path"])

    niq_na = niq_na[niq_na[state_col] == state].reset_index(drop=True)
    niq_provs = niq_provs[niq_provs[state_col] == state].reset_index(drop=True)

    print(f"  [loaded] NIQ-set-1: {len(niq_na)} rows from CSV")
    print(f"  [loaded] NIQ-set-2: {len(niq_provs)} rows from CSV")
    return niq_na, niq_provs


def _load_niq_mock(cfg: dict) -> tuple:
    from mock_data_generator import generate_all_data, save_qes_workbooks, save_niq_workbook

    data = generate_all_data(cfg)
    save_qes_workbooks(data, cfg)
    save_niq_workbook(data, cfg)

    print(f"  [loaded] NIQ-set-1: {len(data['niq_na'])} rows (mock)")
    print(f"  [loaded] NIQ-set-2: {len(data['niq_providers'])} rows (mock)")
    return data["niq_na"], data["niq_providers"]
