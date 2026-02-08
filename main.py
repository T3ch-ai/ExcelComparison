"""
Network Adequacy Comparison Tool -- Main Orchestrator (Phase 2)
===============================================================
Usage:
    python main.py                             # Uses config.yaml in current dir
    python main.py --config path/to/config.yaml
    python main.py --state CA                  # Override state
"""

import argparse
import time

from config_loader import load_config
from data_loader import load_qes_data, load_niq_data
from comparator import compare_network_adequacy
from workbook_builder import build_output_workbook


def main():
    parser = argparse.ArgumentParser(description="Network Adequacy Comparison: QES vs NIQ")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    parser.add_argument("--state", default=None, help="Override state code (e.g. TX, CA)")
    args = parser.parse_args()

    print("=" * 70)
    print("  Network Adequacy Comparison Tool -- Phase 2")
    print("=" * 70)

    # --- Config ---
    print("\n[1/5] Loading configuration...")
    cfg = load_config(args.config)
    if args.state:
        cfg["state"] = args.state
    print(f"  State         : {cfg['state']}")
    print(f"  NIQ Source    : {cfg['niq']['source_type']}")
    print(f"  Compare cols  : {[cc['label'] for cc in cfg['compare_columns']]}")
    print(f"  Chunked load  : {cfg.get('chunked_loading', {}).get('enabled', False)}")
    additional = cfg.get("additional_result_columns", [])
    if additional:
        print(f"  Additional    : {[ac['label'] for ac in additional]}")

    start = time.time()

    # --- Load NIQ (may generate mock data + QES workbooks) ---
    print("\n[2/5] Loading NIQ data...")
    niq_na, niq_providers = load_niq_data(cfg)

    # --- Load QES ---
    print("\n[3/5] Loading QES data...")
    qes_na, qes_providers = load_qes_data(cfg)

    # --- Memory report ---
    _print_memory_report(qes_na, qes_providers, niq_na, niq_providers)

    # --- Compare ---
    print("\n[4/5] Comparing QES vs NIQ...")
    comparison = compare_network_adequacy(qes_na, niq_na, cfg)

    # --- Build Output ---
    print("\n[5/5] Building output workbook...")
    output_path = build_output_workbook(
        qes_na, qes_providers, niq_na, niq_providers, comparison, cfg,
    )

    elapsed = time.time() - start
    print(f"\n{'=' * 70}")
    print(f"  Done in {elapsed:.1f}s  |  Output: {output_path}")
    print(f"{'=' * 70}")
    return output_path


def _print_memory_report(qes_na, qes_providers, niq_na, niq_providers):
    """Print memory usage for each loaded DataFrame."""
    print("\n  Memory Usage:")
    for name, df in [("QES-NA", qes_na), ("QES-Providers", qes_providers),
                     ("NIQ-NA", niq_na), ("NIQ-Providers", niq_providers)]:
        mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        print(f"    {name:15s}: {len(df):>8,} rows, {mem_mb:>8.1f} MB")


if __name__ == "__main__":
    main()
