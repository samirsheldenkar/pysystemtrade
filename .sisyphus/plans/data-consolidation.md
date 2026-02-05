# Data Consolidation & Pipeline Execution

## TL;DR

> **Quick Summary**: Consolidate futures data (Parquet) from 3 disparate sources into a new master folder using a "smart merge" strategy. Conflicts are logged and then enriched using Databento as an external truth source. Finally, run the full pysystemtrade data pipeline (Rolls -> Multiple -> Adjusted).
> 
> **Deliverables**:
> - `consolidate_futures.py`: Smart merge script (Parquet-aware).
> - `verify_conflicts_databento.py`: Script to fetch truth data for flagged conflicts.
> - `/home/samir/data/futures_consolidated/`: Clean, merged dataset.
> - `consolidation_report.csv`: Log of conflicts, enriched with Databento reference data.
> - Updated Roll Calendars, Multiple Prices, and Adjusted Prices.
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: Sequential

---

## Context

### Original Request
User has `futures` (old), `futures_new`, `futures_dev`, and `futures_20251119`. Needs to consolidate all into a single master source and run the pipeline.

### Interview Summary
**Key Decisions**:
- **Source Format**: Parquet (Schema: `OPEN`, `HIGH`, `LOW`, `FINAL`, `VOLUME`; Index: `DatetimeIndex`).
- **Merge Logic**:
  - Union dates.
  - Overlap check: Compare values.
  - Minor Diff: Accept file with later modification time.
  - Major Diff: **FLAG** in report, keep latest file's data.
- **Conflict Resolution**: Use **Databento** to retrieve truth data for conflicts. Reported in `consolidation_report.csv`.
- **Destination**: `/home/samir/data/futures_consolidated`.

---

## Work Objectives

### Core Objective
Create a unified futures dataset, identify/verify data conflicts using Databento, and generate downstream data products.

### Concrete Deliverables
- [ ] `consolidate_futures.py` (Parquet support)
- [ ] `verify_conflicts_databento.py` (Databento integration)
- [ ] `futures_consolidated` folder
- [ ] `consolidation_report.csv` (Enriched)
- [ ] Roll Calendars, Multiple Prices, Adjusted Prices (Regenerated)

---

## Verification Strategy

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Agent-Executed QA Scenarios

**Scenario 1: Verify Parquet Consolidation**
- Tool: `interactive_bash`
- Steps:
  1. Create dummy Parquet files in `temp_A/` and `temp_B/` with known overlapping data/conflict.
  2. Run `consolidate_futures.py`.
  3. Assert `futures_consolidated/dummy.parquet` exists and is valid Parquet.
  4. Assert `consolidation_report.csv` flags the conflict.

**Scenario 2: Verify Databento Integration**
- Tool: `interactive_bash`
- Steps:
  1. Create a dummy `consolidation_report.csv` with one known contract/date (e.g., ES, 2023-01-01).
  2. Mock Databento API (or use provided key if available in env).
  3. Run `verify_conflicts_databento.py`.
  4. Assert report is updated with `Ref_Open` etc.

---

## Execution Strategy

```
Wave 1 (Tools):
├── Task 1: Create Consolidate Script (Parquet)
└── Task 2: Create Databento Verification Script

Wave 2 (Data Ops):
├── Task 3: Run Consolidation
└── Task 4: Run Conflict Verification (Databento)

Wave 3 (Pipeline):
├── Task 5: Generate Roll Calendars
├── Task 6: Generate Multiple Prices
└── Task 7: Generate Adjusted Prices
```

---

## TODOs

- [ ] 1. Create Smart Consolidation Script (Parquet)

  **What to do**:
  - Create `sysinit/futures/consolidate_futures.py`.
  - Implement `FuturesConsolidator` class:
    - **Input**: Parquet files.
    - **Columns**: `OPEN`, `HIGH`, `LOW`, `FINAL`, `VOLUME`.
    - **Logic**:
      - Read all source Parquet files for a contract.
      - Align on `index` (Datetime).
      - Check overlaps.
      - If diff > `1e-6`: Log to `consolidation_report.csv` (Contract, Date, FileA_Val, FileB_Val, SourceA, SourceB).
      - Merge strategy: Take data from file with latest `mtime`.
      - Write to `/home/samir/data/futures_consolidated/{contract}.parquet`.

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
  - **Skills**: [`python-pandas`]

  **Acceptance Criteria**:
  - [ ] Script handles Parquet I/O correctly.
  - [ ] Conflicts logged to CSV.
  - [ ] Output is valid Parquet with correct schema.

- [ ] 2. Create Databento Verification Script

  **What to do**:
  - Create `sysinit/futures/verify_conflicts_databento.py`.
  - Inputs: `consolidation_report.csv`, API Key (env var `DATABENTO_API_KEY`).
  - Logic:
    - Read conflict report.
    - Group by Contract.
    - For each conflict date:
      - Call Databento API (Historical Bars).
      - Fetch OHLCV for that specific contract/date.
    - Append `Ref_Open`, `Ref_High`, `Ref_Low`, `Ref_Close`, `Ref_Vol` to the report.
    - Save as `consolidation_report_verified.csv`.

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
  - **Skills**: [`python`]

  **References**:
  - `databento` python library docs.

  **Acceptance Criteria**:
  - [ ] Script reads conflict report.
  - [ ] Fetches data (mocked or real).
  - [ ] Writes enriched CSV.

- [ ] 3. Run Consolidation on Full Dataset

  **What to do**:
  - Execute `consolidate_futures.py` targeting the 4 source folders.
  - Ensure `/home/samir/data/futures_consolidated` is created.

  **Recommended Agent Profile**:
  - **Category**: `quick`

- [ ] 4. Run Conflict Verification

  **What to do**:
  - Check if `consolidation_report.csv` has entries.
  - If yes, ask user for `DATABENTO_API_KEY` (if not set).
  - Run `verify_conflicts_databento.py`.

  **Recommended Agent Profile**:
  - **Category**: `quick`

- [ ] 5. Generate Roll Calendars (New Data)

  **What to do**:
  - Use `sysinit/futures/rollcalendars_from_providedcsv_prices.py` (modified for Parquet or check if it supports generic loader).
  - *Correction*: `sysinit` scripts might expect CSV or DB.
  - **Action**: Create a runner `sysinit/futures/generate_rolls_from_parquet.py` that adapts the logic to read Parquet source and invoke `build_and_write_roll_calendar`.
  - Or convert Parquet -> Temp CSV -> Run Standard Script -> Delete Temp.
  - **Decision**: Adapter script `sysinit/futures/run_pipeline_parquet.py` that handles the IO impedance mismatch if necessary, or extends `FuturesData` to read Parquet.
  - *Note*: Existing system likely has `FuturesData` class. We should check if it supports Parquet. If not, we might need to add support or do the conversion.
  - *Assumption*: We will check `sysdata` for parquet support (saw `parquet_multiple_prices.py` in search). `futures_contract_prices` might be CSV-only in legacy code.
  - **Sub-task**: Verify if `sysdata.futures.futures_contract_prices` supports parquet. If not, `consolidate_futures.py` should ALSO output CSVs for compatibility, OR we patch the system.
  - **Decision for now**: Output Parquet (as requested) AND CSV (for compatibility if needed). Or stick to Parquet if the "New" folders imply the system is moving that way.
  - *Refined*: User has "futures_new" (Parquet). Original "futures" had CSVs? Wait, search results for original `futures` folder showed Parquet files too! (`/home/samir/data/futures/futures_contract_prices/HOUSE-DC#20250200.parquet`). So the system ALREADY supports Parquet.
  - **Conclusion**: System supports Parquet. Just use standard scripts pointing to new folder.

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`

- [ ] 6. Generate Multiple Prices

  **What to do**:
  - Run `process_multiple_prices` logic.

- [ ] 7. Generate Adjusted Prices

  **What to do**:
  - Run `process_adjusted_prices` logic.

---

## Success Criteria

- [ ] `futures_consolidated` contains merged Parquet files.
- [ ] `consolidation_report_verified.csv` contains conflicts + Databento truth.
- [ ] Downstream data (Rolls, Multi, Adj) generated successfully.
