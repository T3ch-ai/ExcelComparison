"""
Configuration loader and validator.
"""

import os
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    _validate(cfg)
    # Ensure labels have defaults
    labels = cfg.setdefault("output", {}).setdefault("labels", {})
    defaults = {
        "match": "MATCH", "mismatch": "MISMATCH", "warning": "WARNING",
        "overall_match": "MATCH", "overall_mismatch": "MISMATCH",
        "overall_qes_only": "QES ONLY", "overall_niq_only": "NIQ ONLY",
        "na_qes_only": "N/A - QES Only", "na_niq_only": "N/A - NIQ Only",
        "null_vs_value": "NULL vs value",
    }
    for k, v in defaults.items():
        labels.setdefault(k, v)
    cfg.setdefault("additional_result_columns", [])
    return cfg


def _validate(cfg: dict):
    required_top = ["state", "qes", "niq", "key_columns", "compare_columns", "drilldown", "output"]
    for k in required_top:
        assert k in cfg, f"Missing required config key: {k}"
    assert len(cfg["key_columns"]["qes"]) == len(cfg["key_columns"]["niq"]), \
        "key_columns qes and niq must have the same number of entries"
    for cc in cfg["compare_columns"]:
        assert "qes_col" in cc and "niq_col" in cc, \
            f"Each compare_column must have qes_col and niq_col: {cc}"
    assert cfg["niq"]["source_type"] in ("rds", "mock", "csv", "excel"), \
        f"niq.source_type must be rds, mock, csv, or excel -- got {cfg['niq']['source_type']}"


def get_rds_password(cfg: dict) -> str:
    env_var = cfg["niq"]["rds"].get("password_env_var", "NIQ_RDS_PASSWORD")
    pwd = os.environ.get(env_var)
    if not pwd:
        raise EnvironmentError(f"RDS password not found. Set env var: {env_var}")
    return pwd


def get_rds_connection_string(cfg: dict) -> str:
    rds = cfg["niq"]["rds"]
    engine = rds.get("engine", "mysql")
    driver = "pymysql" if engine == "mysql" else "psycopg2"
    dialect = f"{engine}+{driver}"
    pwd = get_rds_password(cfg)
    return f"{dialect}://{rds['username']}:{pwd}@{rds['host']}:{rds['port']}/{rds['database']}"
