## Plan Generated: Data Consolidation & Pipeline

**Key Decisions Made:**
- **Merge Strategy**: Smart Merge (Union, Overlap Check, Latest Wins on Conflict).
- **Conflict Handling**: Discrepancies > `1e-6` are flagged. **Databento** used to verify/enrich conflicts in a post-merge step.
- **Data Format**: **Parquet** (Verified schema: `OPEN`, `HIGH`, `LOW`, `FINAL`, `VOLUME`, `DatetimeIndex`).
- **Destination**: `/home/samir/data/futures_consolidated`.

**Scope:**
- IN: Consolidation script (Parquet), Databento Verification script, Pipeline execution.
- OUT: Manual resolution (User provided with enriched report).

**Guardrails Applied:**
- **Memory Safety**: Process per-contract.
- **Verification**: Post-hoc verification with external truth source (Databento).

**Auto-Resolved:**
- [Schema]: Parquet files in all source folders have identical schema.
- [System Compatibility]: Existing `futures` folder also contained Parquet, implying system compatibility.

**Decisions Needed:**
- None. Requirements clear.
- **Momus Review**: [OKAY] - Plan approved.

Plan saved to: `.sisyphus/plans/data-consolidation.md`
