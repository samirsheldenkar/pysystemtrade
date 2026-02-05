## Plan Generated: Data Consolidation & Pipeline

**Key Decisions Made:**
- **Roll Logic**: Switched to **Volume/OI based** rolling with **Fixed Date Backstop**.
  - Current system (price-only) does not support this.
  - Will build `build_roll_calendars_custom.py` to implement this algo.
- **Output Format**: Roll calendars to CSV (compatible with existing `roll_calendars_from_db`).
- **Data Source**: Parquet files (Schema verified).
- **Merge**: Custom Roll Calendars will merge/append to existing CSVs in `roll_calendars_from_db`.

**Scope:**
- IN: `consolidate_futures.py`, `verify_conflicts_databento.py`, `build_roll_calendars_custom.py` (New Algo).
- OUT: Modifying core system classes (We will use a standalone script for the custom logic to avoid regression).

**Guardrails Applied:**
- **Verification**: Custom roll logic will be verified against dummy Volume/OI data to ensure crossover logic works.

**Decisions Needed:**
- None. Plan updated to reflect user review.

Plan saved to: `.sisyphus/plans/data-consolidation.md`
