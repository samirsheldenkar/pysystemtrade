# Draft: Data Pipeline & Consolidation Plan

## Requirements (confirmed)
- Source Data Locations:
  - `/home/samir/data/futures`
  - `/home/samir/data/futures_new`
  - `/home/samir/data/futures_dev`
  - `/home/samir/data/futures_20251119`
- Goal:
  1. **Consolidate** all sources into `/home/samir/data/futures_consolidated`.
  2. **Smart Merge Logic** (User Mandate):
     - **Partial History**: Union distinct dates.
     - **Overlap**: Compare values.
     - **Minor Diff**: Accept later timestamp file (file mod time).
     - **Major Diff**: **FLAG** in report (do not auto-merge conflicting rows, or keep existing and log warning). *Decision: Log to `conflicts.csv` and keep latest file's data for now to allow pipeline to proceed, but mark for review.*
  3. **Pipeline Execution**:
     - Generate Roll Calendars (`sysinit.futures.build_roll_calendars`).
     - Generate Multiple Prices.
     - Generate Adjusted Prices.
- **Critical Check Passed**: `/home/samir/data` is accessible and contains all folders.

## Technical Decisions
- **Merge Script**: Custom Python script (`consolidate_futures.py`).
  - Uses `pandas` to read CSVs.
  - Index: `Date`.
  - Columns to check: `Open`, `High`, `Low`, `Close`, `Volume`.
  - Output: `/home/samir/data/futures_consolidated`.
  - Report: `/home/samir/data/consolidation_report.txt`.
- **Pipeline Scripts**:
  - `sysinit.futures.rollcalendars_from_db_prices_to_csv`
  - `sysinit.futures.multipleprices_from_db_prices_and_csv_calendars_to_db`
  - `sysinit.futures.adjustedprices_from_db_multiple_to_db`

## Scope Boundaries
- INCLUDE: Consolidation script, Roll calendar generation, Price stitching, Adjustment generation.
- EXCLUDE: Manual fixing of flagged conflicts (User must review report).
- EXCLUDE: Updating `sysdata` config to point to new folder (User will manually verify first).
