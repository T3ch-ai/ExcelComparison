# Network Adequacy Comparison Tool -- Phase 1

## Overview

Enterprise-grade Python tool that compares Network Adequacy data between:
- **QES** (Quality Evaluation System): Two Excel workbooks (summary + providers)
- **NIQ** (New Internal Query): Configurable source -- Excel workbook, RDS, CSV, or mock

Produces a single output Excel workbook with comparison results, raw data sheets,
additional contextual columns, and clickable drill-down to provider-level detail.

## What Changed (v2)

| # | Change | Details |
|---|--------|---------|
| 1 | No unicode | All flags use plain ASCII: MATCH, MISMATCH, WARNING, QES ONLY, NIQ ONLY |
| 2 | NIQ from Excel | NIQ source is now configurable: single workbook with 2 sheets, two separate workbooks, RDS, CSV, or mock |
| 3 | Different column names | QES and NIQ column names are fully independent and mapped in config |
| 4 | Additional result columns | Non-compared columns (e.g. Member Count) can be pulled from either/both datasets into results |
| 5 | Configurable result order | result_column_order in config controls exact column layout of the comparison sheet |

## Architecture

```
config.yaml              -- All settings, column mappings, source config
main.py                  -- CLI orchestrator
config_loader.py         -- YAML loading + validation
data_loader.py           -- Excel / RDS / CSV / Mock loader
mock_data_generator.py   -- Synthetic test data
comparator.py            -- Core diff engine with additional columns
workbook_builder.py      -- Output Excel with formatting + hyperlinks
```

## Quick Start

```bash
pip install openpyxl pyyaml pandas sqlalchemy pymysql

cd network_adequacy_comparator
python main.py                      # Runs with mock data
python main.py --state CA           # Override state
python main.py --config my.yaml     # Custom config
```

## NIQ Source Configuration

### Option A: Single Excel workbook with two sheets (default)

```yaml
niq:
  source_type: "excel"
  excel:
    single_workbook: true
    workbook_path: "input/NIQ_Data.xlsx"
    network_adequacy_sheet: "NetworkAdequacy"
    provider_detail_sheet: "ProviderDetail"
```

### Option B: Two separate Excel workbooks

```yaml
niq:
  source_type: "excel"
  excel:
    single_workbook: false
    workbook1_path: "input/NIQ_Summary.xlsx"
    workbook1_sheet: "Sheet1"
    workbook2_path: "input/NIQ_Providers.xlsx"
    workbook2_sheet: "Sheet1"
```

### Option C: Amazon RDS

```yaml
niq:
  source_type: "rds"
  rds:
    host: "your-cluster.us-east-1.rds.amazonaws.com"
    port: 3306
    database: "network_adequacy_db"
    username: "readonly_user"
    password_env_var: "NIQ_RDS_PASSWORD"
    engine: "mysql"
    network_adequacy_query: "SELECT ... WHERE state_code = :state"
    provider_detail_query: "SELECT ... WHERE state_code = :state"
```

### Option D: CSV files

```yaml
niq:
  source_type: "csv"
  csv:
    network_adequacy_path: "input/NIQ_NA.csv"
    provider_detail_path: "input/NIQ_Provs.csv"
```

## Column Mapping

QES and NIQ have completely different column names. The config maps them:

```yaml
key_columns:
  qes: ["State",        "County_Name", "Specialty"]
  niq: ["state_code",   "county_name", "specialty_type"]

compare_columns:
  - qes_col: "Provider_Count"       # QES column name
    niq_col: "provider_cnt"          # NIQ column name (different!)
    label: "Provider Count"          # Display label in results
    dtype: "numeric"
    tolerance: 0                     # Exact match

  - qes_col: "Meets_Standard"
    niq_col: "meets_standard_flag"
    label: "Meets Standard"
    dtype: "text"
```

## Additional (Non-Compared) Columns

Columns that appear in results for context but are NOT diffed:

```yaml
additional_result_columns:
  - qes_col: "Member_Count"         # from QES dataset
    niq_col: "member_count"          # from NIQ dataset
    label: "Member Count"

  # Column only in one dataset:
  - qes_col: null
    niq_col: "last_refreshed"
    label: "Last Refreshed (NIQ)"
```

These produce two columns in results: QES_Member Count and NIQ_Member Count.

## Result Column Order

Controls the exact layout of the Comparison_Results sheet:

```yaml
result_column_order:
  - "{keys}"                             # State, County_Name, Specialty
  - "{row_source}"                       # Both / QES Only / NIQ Only
  - "{compare:Provider Count}"           # QES_, NIQ_, Diff_, Match_ columns
  - "{additional:Member Count}"          # QES_, NIQ_ columns (no diff)
  - "{compare:Meets Standard}"
  - "{compare:Avg Distance (Miles)}"
  - "{overall_match}"                    # MATCH / MISMATCH / QES ONLY / NIQ ONLY
```

## Output Workbook Structure

| Sheet | Description |
|-------|-------------|
| Summary | Dashboard: match rate, mismatch counts by column |
| Comparison_Results | Full diff with hyperlinks, auto-filter, color coding |
| QES_Network_Adequacy | Raw QES-set-1 |
| QES_Providers | Raw QES-set-2 |
| NIQ_Network_Adequacy | Raw NIQ-set-1 |
| NIQ_Providers | Raw NIQ-set-2 |
| QES_Harris_Cardiology (etc.) | Drill-down: providers for that county+specialty |
| NIQ_Harris_Cardiology (etc.) | Same for NIQ |

### Drill-Down Behavior

In Comparison_Results, the Provider Count cells are blue hyperlinks.
Clicking "15" under QES_Provider Count jumps to sheet QES_Harris_Cardiology
showing those 15 providers. Each drill-down has a "<< Back" link.

### Color Coding

| Color | Meaning |
|-------|---------|
| Green background | MATCH |
| Red background | MISMATCH |
| Orange background | QES ONLY (row exists only in QES) |
| Light blue background | NIQ ONLY (row exists only in NIQ) |
| Blue underlined text | Clickable hyperlink to drill-down |

### Match Flag Labels (Plain ASCII)

| Label | Used When |
|-------|-----------|
| MATCH | Column values are equal (within tolerance) |
| MISMATCH | Column values differ |
| WARNING | Row is in only one dataset |
| QES ONLY | Overall flag for QES-only rows |
| NIQ ONLY | Overall flag for NIQ-only rows |

## Assumptions

1. QES is always provided as Excel workbooks (two files)
2. NIQ source is configurable (Excel / RDS / CSV / Mock)
3. Composite join key is (State, County, Specialty) -- configurable
4. Single state per execution run
5. Sheet names truncated to 31 chars (Excel limit)
6. Max 200 drill-down sheets (configurable)
7. RDS password from environment variable (never in config)
8. All flag text is plain ASCII (no unicode symbols)

## Phase 2 (Planned)

React web application for interactive viewing with filters, expand/collapse,
and visual diff. Will reuse the same config.yaml and comparison engine.
