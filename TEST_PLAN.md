# Network Adequacy Comparison Tool -- Test Plan

## Environment Setup

### Prerequisites
- Python 3.10+
- Virtual environment with dependencies installed

### Setup Steps
```bash
# Option A: Using setup.sh (Linux/macOS)
chmod +x setup.sh && ./setup.sh

# Option B: Manual setup (any OS)
python -m venv .venv

# Activate:
#   Windows:    .venv\Scripts\activate
#   Linux/Mac:  source .venv/bin/activate

pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests via notebook script (recommended)
python notebook_steps_2.py

# Run full pipeline via CLI
python main.py
python main.py --state CA
```

---

## Test Sections

### Section 1: Environment and Imports
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | Import all modules (`config_loader`, `data_loader`, `comparator`, `workbook_builder`, `mock_data_generator`) | `Imports OK` printed, no `ImportError` |
| 1.2 | Print Python and pandas versions | Version strings displayed |
| 1.3 | Optional `python-dotenv` import | Loads if installed, prints info message if not (does not crash) |

### Section 2: Configuration Loading
| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Load `config.yaml` via `load_config()` | No errors; returns dict |
| 2.2 | Verify `state` field | Prints configured state (e.g., `TX`) |
| 2.3 | Verify `key_columns` | QES and NIQ key lists printed, same length (3 each) |
| 2.4 | Verify `compare_columns` | 3 columns listed: Coverage Percentage (numeric, direction), Servicing Providers (numeric), Access Met (text, value_map) |
| 2.5 | Verify `additional_result_columns` | 9 additional columns listed with QES/NIQ mappings |
| 2.6 | Verify `drilldown` config | `link_column`, QES/NIQ provider keys printed |
| 2.7 | Verify `chunked_loading` config | `enabled`, `chunk_size`, `threshold_mb` printed |
| 2.8 | Verify `labels` | `higher=HIGHER`, `lower=LOWER`, `same=SAME`, match/no_match indicators printed |

### Section 3: Mock Data Generation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Generate mock data via `generate_all_data(cfg)` | Returns dict with 4 DataFrames |
| 3.2 | Inspect QES-NA DataFrame | Shape ~144 rows x 23 cols; columns include `Project Name`, `CountySSA`, `FIPS County`, `County Name`, `% members with Access`, etc. |
| 3.3 | Inspect QES-Providers DataFrame | Shape ~3,800 rows x 34 cols; columns include `NPI`, `TaxID`, `Latitude`, `Longitude`, `Taxonomy`, etc. |
| 3.4 | Inspect NIQ-NA DataFrame | Shape ~148 rows x 17 cols; columns include `state`, `countSSACode`, `coverage_percentage`, etc. |
| 3.5 | Inspect NIQ-Providers DataFrame | Shape ~3,800 rows x 34 cols; lowercase column names |
| 3.6 | Verify SSA codes | All SSA codes start with correct state prefix (TX=45, WI=52) |
| 3.7 | Verify SSA != FIPS | SSA prefix differs from FIPS prefix (TX: SSA=45, FIPS=48) |
| 3.8 | Verify county classifications | Mix of Metro/Rural/CEAC; Metro most common |
| 3.9 | Verify specialty codes | 10 distinct specialties with codes and names |
| 3.10 | Verify provider entity types | Mix of Individual (~85%) and Organization (~15%) |
| 3.11 | Verify facility providers | Organization records have `Facility Name` populated |
| 3.12 | Verify lat/long ranges | Within expected bounds for configured state |
| 3.13 | Verify NPI format | All NPIs are exactly 10 digits |
| 3.14 | Verify TIN format | All TINs are exactly 9 digits |

### Section 3b: Save Mock Data
| Step | Action | Expected Result |
|------|--------|-----------------|
| 3b.1 | `save_qes_workbooks(data, cfg)` | Creates `input/QES_Network_Adequacy.xlsx` and `input/QES_Providers.xlsx` |
| 3b.2 | `save_niq_workbook(data, cfg)` | Creates `input/NIQ_Data.xlsx` with `NetworkAdequacy` and `ProviderDetail` sheets |

### Section 4: Data Loading (Round-Trip)
| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Load NIQ data via `load_niq_data(cfg)` | Returns 2 DataFrames matching generated row counts |
| 4.2 | Load QES data via `load_qes_data(cfg)` | Returns 2 DataFrames; reads from saved Excel files |
| 4.3 | Verify shapes match generation | QES-NA, QES-Providers, NIQ-NA, NIQ-Providers shapes printed |
| 4.4 | Print memory usage | Memory in MB for each DataFrame |

### Section 5: Comparison Engine
| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Run `compare_network_adequacy(qes_na, niq_na, cfg)` | Returns DataFrame with ~150 rows, 36 columns |
| 5.2 | Verify comparison summary | Prints: Total rows, Matched/Mismatched counts with percentages, QES Only, NIQ Only counts |
| 5.3 | Verify Direction column | `Direction_Coverage Percentage` has values: SAME (~131), HIGHER (~6), LOWER (~5) |
| 5.4 | Inspect HIGHER rows | Shows rows where NIQ coverage > QES coverage (positive diff) |
| 5.5 | Inspect LOWER rows | Shows rows where NIQ coverage < QES coverage (negative diff) |
| 5.6 | Inspect QES Only rows | Rows present in QES but missing from NIQ (~2 rows) |
| 5.7 | Inspect NIQ Only rows | Rows present in NIQ but missing from QES (~6 rows) |

### Section 6: Summary Statistics
| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Unique county count | Number of distinct counties in comparison |
| 6.2 | Unique NPI counts | QES and NIQ unique NPI counts from provider data |
| 6.3 | Specialty breakdown | Per-specialty: Match count, QES>NIQ count, NIQ>QES count |
| 6.4 | Zero serving counts | QES and NIQ rows with 0 servicing providers |

### Section 7: Output Workbook
| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Build output workbook | File created: `output/Network_Adequacy_Comparison_{STATE}_{TIMESTAMP}.xlsx` |
| 7.2 | Verify sheet count | ~145 sheets (Summary + Comparison_Results + drill-downs + raw data) |
| 7.3 | Verify Summary sheet | Contains county counts, NPI counts, specialty breakdown |
| 7.4 | Verify Comparison_Results sheet | ~151 rows, 36 columns, frozen header, auto-width |
| 7.5 | Verify drill-down sheets | QES and NIQ sheets per county+specialty, cross-linked |
| 7.6 | Verify hyperlinks | `Diff_Coverage Percentage` cells link to drill-down sheets |
| 7.7 | Verify RED highlighting | Diff and Direction columns highlighted RED for deviations from QES |
| 7.8 | Verify MATCH highlighting | Match cells highlighted GREEN, mismatch RED |

---

## Component Tests (Section 8)

These are automated assertions that run as part of `notebook_steps_2.py`.

| Test | Name | What It Validates | Assertions |
|------|------|-------------------|------------|
| 1 | Direction indicator logic | `_compute_direction()` returns correct HIGHER/LOWER/SAME | NIQ>QES=HIGHER, QES>NIQ=LOWER, equal=SAME, within tolerance=SAME, None input="" |
| 2 | Normalize value | `_normalize_value()` handles percentages and types | "95.5%"->95.5, 95.5->95.5, "hello"->"hello", None->None |
| 3 | Join key normalization | `_normalize_key_part()` handles Excel leading-zero stripping | "011"->"11", 11->"11", "007"->"7", "45130"->"45130", "TX"->"TX" |
| 4 | Config loader defaults | `load_config()` sets default labels and sections | `higher`, `lower`, `same` in labels; `chunked_loading` present |
| 5 | QES-NA column completeness | Generated QES-NA has all required columns | 13 required columns verified present |
| 6 | QES-Provider column completeness | Generated QES-Providers has all required columns | 9 required columns verified present (NPI, TaxID, Lat, Lon, Taxonomy, Gender, etc.) |
| 7 | NIQ-NA column completeness | Generated NIQ-NA has all required columns | 11 required columns verified present |
| 8 | SSA differs from FIPS | SSA codes use different numbering than FIPS | Every SSA code differs from corresponding FIPS code |
| 9 | NPI/TIN format | Provider identifiers have correct lengths | All NPI=10 digits, all TIN=9 digits |
| 10 | Both rows after round-trip | Comparison produces matched rows after Excel save/load | Both row count > 0 (join key normalization works) |
| 11 | Deterministic repeatability | Same seed produces identical output | Two runs with same config produce `equals()` DataFrames |
| 12 | Synthetic fallback | Mock data works for non-hardcoded states | CA: valid data with SSA prefix 06, 5-digit ZIPs; XX: raises ValueError |
| 13 | QES CSV loading | QES data loads from CSV files | Explicit `source_type: csv` and auto-detect from `.csv` extension both produce correct shapes |
| 14 | Compact config normalization | Compact `additional_result_columns` format normalizes correctly | All entries have `qes_col`, `niq_col`, and non-empty `label` after normalization |

---

## Performance Test (Section 9)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | Generate large dataset | Replicate NIQ providers 100x (~387,700 rows) |
| 9.2 | Save to CSV | Creates file (~110 MB) |
| 9.3 | Load via `_load_csv_chunked()` | Reads in 10K-row chunks with progress reporting |
| 9.4 | Verify row count | Loaded row count matches original |
| 9.5 | Cleanup | Temporary CSV file deleted |

---

## Manual Verification Checklist

After running the notebook or `main.py`, open the output Excel file and verify:

- [ ] **Summary sheet**: 5 sections visible, left-aligned, county counts and NPI counts correct
- [ ] **Comparison_Results sheet**: Header row frozen, auto-filtered, columns in configured order
- [ ] **Direction column**: HIGHER/LOWER/SAME values present with correct RED/GREEN fills
- [ ] **Diff column**: Non-zero values highlighted RED; clickable hyperlinks to drill-down sheets
- [ ] **Drill-down sheets**: QES and NIQ paired sheets; "See NIQ Providers" / "See QES Providers" cross-links; "Back to Comparison Results" link
- [ ] **Raw data sheets**: QES_Network_Adequacy, QES_Providers, NIQ_Network_Adequacy, NIQ_Providers with full column sets
- [ ] **QES Only / NIQ Only rows**: Highlighted with distinct fill colors (orange / blue)
- [ ] **Access Met column**: value_map applied (Y->Met, N->Not Met for QES; Met/Not Met from NIQ)
- [ ] **Output filename**: Includes state code and timestamp (e.g., `..._TX_20260208_120041.xlsx`)

---

## State Portability Tests

| State | Type | Expected Behavior |
|-------|------|-------------------|
| TX | Hardcoded (verified SSA/FIPS from NBER) | Full pipeline with 18 real counties, SSA prefix 45, FIPS prefix 48 |
| WI | Hardcoded (verified SSA/FIPS from NBER) | Full pipeline with 20 real counties, SSA prefix 52, FIPS prefix 55 |
| CA | Synthetic fallback | Generates ~20 synthetic counties, SSA prefix 06, FIPS prefix 06, prints info message |
| CT | Synthetic fallback | ZIP codes zero-padded to 5 digits (06xxx range) |
| NY | Synthetic fallback | Generates valid synthetic data |
| XX | Invalid | Raises `ValueError: Unknown state code` |

To run portability tests:
```bash
python main.py --state TX
python main.py --state WI
python main.py --state CA
python main.py --state NY
```

---

## Edge Cases Covered

1. **Excel strips leading zeros**: Specialty code "011" becomes integer 11 after Excel round-trip. Join key normalization in `comparator.py` handles this.
2. **Percentage string normalization**: "95.5%" string and 95.5 float both normalize to 95.5.
3. **value_map harmonization**: QES "Y"/"N" maps to "Met"/"Not Met" for comparison with NIQ.
4. **NULL vs value**: When one source has data and the other has NULL, flagged as "NULL vs value".
5. **Duplicate join keys**: If multiple rows match same key, first row is used.
6. **Zero-padded ZIP codes**: States with low ZIP ranges (CT, MA, NH, RI, VT, ME) produce 5-digit zero-padded strings.
7. **Large files**: Provider files >100MB loaded in configurable chunks to manage memory.

---

## Last Verified Run

- **Date**: 2026-02-08
- **State**: TX
- **Results**: 14/14 component tests PASSED, large file test PASSED
- **Output**: `output/Network_Adequacy_Comparison_TX_20260208_122317.xlsx` (145 sheets)
- **Summary**: 150 rows, 142 Both (85.2% match), 2 QES Only, 6 NIQ Only
