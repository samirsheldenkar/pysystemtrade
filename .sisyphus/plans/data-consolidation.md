# Data Consolidation & Pipeline Execution

## TL;DR

> **Quick Summary**: Consolidate futures data (Parquet) from 3 disparate sources into a new master folder using a "smart merge" strategy. Conflicts are logged and then enriched using Databento. **CRITICAL UPDATE**: Implement custom Roll Calendar logic (Volume/OI based + Fixed Date backstop) as standard system logic does not support this.
> 
> **Deliverables**:
> - `consolidate_futures.py`: Smart merge script (Parquet-aware).
> - `verify_conflicts_databento.py`: Script to fetch truth data for flagged conflicts.
> - `build_roll_calendars_custom.py`: **NEW** script implementing Volume/OI + Backstop logic.
> - `/home/samir/data/futures_consolidated/`: Clean, merged dataset.
> - `consolidation_report.csv`: Log of conflicts.
> - Updated Roll Calendars, Multiple Prices, and Adjusted Prices.
> 
> **Estimated Effort**: High (Custom Algo Dev)
> **Parallel Execution**: Sequential

---

## Context

### Original Request
User has `futures` (old), `futures_new`, `futures_dev`, and `futures_20251119`. Needs to consolidate all into a single master source and run the pipeline.

### Interview Summary
**Key Decisions**:
- **Source Format**: Parquet (Schema: `OPEN`, `HIGH`, `LOW`, `FINAL`, `VOLUME`, `DatetimeIndex`).
- **Merge Logic**: Smart Merge (Union, Overlap Check, Latest Wins on Conflict).
- **Roll Logic (NEW)**:
  - **Volume/OI Switch**: Roll when new contract Vol/OI > old contract.
  - **Use calculated fixed date as guide**: If not within 5 days of the calculated desired data, then wait.
  - **Backstop**: Force roll at fixed date if Volume/OI condition not met.
  - **Output**: CSV to `/home/samir/data/futures_consolidated/roll_calendars/`.
  - **Merge**: Must merge with existing `roll_calendars_from_db` CSVs.
- **Destination**: `/home/samir/data/futures_consolidated`.

### Metis Review (Implicit)
**Identified Gaps**:
- **Logic Gap**: Existing `sysinit.futures.build_roll_calendars` is Price-only. User requires Volume/OI logic. This requires writing a **new algorithm**.
- **Data Gap**: Existing Parquet files must contain `VOLUME` (Confirmed) and `OI` (Open Interest - **Needs Verification**).

---

## Work Objectives

### Core Objective
Create a unified futures dataset, identify conflicts, and generate **custom** roll calendars based on liquidity logic.

### Concrete Deliverables
- [ ] `consolidate_futures.py`
- [ ] `verify_conflicts_databento.py`
- [ ] `build_roll_calendars_custom.py` (**New Algo**)
- [ ] `futures_consolidated` folder
- [ ] Roll Calendars (CSV)
- [ ] Multiple/Adjusted Prices

---

## Verification Strategy

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Agent-Executed QA Scenarios

**Scenario 1: Verify Custom Roll Logic**
- Tool: `interactive_bash`
- Steps:
  1. Create dummy price/vol data for Contract A (Dec) and Contract B (Mar).
  2. Set Vol(A) > Vol(B) until Date X, then Vol(B) > Vol(A).
  3. Run `build_roll_calendars_custom.py`.
  4. Assert Roll Date == Date X (Liquidity crossover).
  5. Test Backstop: Set Vol(A) > Vol(B) always, but Backstop = Date Y.
  6. Assert Roll Date == Date Y (Forced roll).

---

## Execution Strategy

```
Wave 1 (Tools):
├── Task 1: Create Consolidate Script (Parquet)
├── Task 2: Create Databento Verification Script
└── Task 3: Create Custom Roll Calendar Script (The hard part)

Wave 2 (Data Ops):
├── Task 4: Run Consolidation
└── Task 5: Run Conflict Verification (Databento)

Wave 3 (Pipeline):
├── Task 6: Generate Custom Roll Calendars
├── Task 7: Generate Multiple Prices
└── Task 8: Generate Adjusted Prices
```

---

## TODOs

- [ ] 1. Create Smart Consolidation Script (Parquet)

  **What to do**:
  - Create `sysinit/futures/consolidate_futures.py`.
  - Implement `FuturesConsolidator` class:
    - **Input**: Parquet files.
    - **Columns**: `OPEN`, `HIGH`, `LOW`, `FINAL`, `VOLUME`. **CHECK FOR OI**.
    - **Logic**: Union dates, check overlaps, merge.
    - **Output**: `/home/samir/data/futures_consolidated/{contract}.parquet`.

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
  - **Skills**: [`python-pandas`]

- [ ] 2. Create Databento Verification Script

  **What to do**:
  - Create `sysinit/futures/verify_conflicts_databento.py`.
  - Fetch truth data for conflicts.

- [ ] 3. Create Custom Roll Calendar Script (Volume/OI + Backstop)

  **What to do**:
  - Create `sysinit/futures/build_roll_calendars_custom.py`.
  - Logic:
    - Load prices + Volume + OI for all contracts of an instrument.
    - For each contract pair (Current, Next):
      - Determine **Liquidity Crossover Date**: First date where `Next.Volume > Current.Volume` (and/or OI).
      - Determine **Backstop Date**: Fixed days before expiry (e.g., First Notice Day).
      - **Roll Date** = `min(Liquidity_Crossover, Backstop)`.
    - Generate `roll_calendar` DataFrame (Date, Contract, Carry).
    - Output to CSV in `/home/samir/data/futures_consolidated/roll_calendars/`.
    - **Merge**: If file exists in `roll_calendars_from_db`, merge new rows (prefer new logic?). User said "merge with these". We will append/update.

  **Recommended Agent Profile**:
  - **Category**: `ultrabrain`
  - **Skills**: [`python-pandas`]

- [ ] 4. Run Consolidation on Full Dataset

  **What to do**:
  - Execute `consolidate_futures.py`.

- [ ] 5. Run Conflict Verification

  **What to do**:
  - Run `verify_conflicts_databento.py`.

- [ ] 6. Generate Custom Roll Calendars

  **What to do**:
  - Run `sysinit/futures/build_roll_calendars_custom.py` for all instruments.

- [ ] 7. Generate Multiple Prices

  **What to do**:
  - Run `process_multiple_prices` logic.

- [ ] 8. Generate Adjusted Prices

  **What to do**:
  - Run `process_adjusted_prices` logic.

---

## Success Criteria

- [ ] Custom Roll Calendars generated using Volume/OI logic.
- [ ] `futures_consolidated` contains merged Parquet files.
- [ ] Pipeline runs end-to-end.
