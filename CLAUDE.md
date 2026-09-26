# NYC Crane Logistics Cartogram

Portfolio data-viz project: an interactive cartogram of NYC where neighborhoods are stretched or squeezed by how hard and expensive it is to deploy a crane there (permit friction + crane cost + street access), instead of by physical distance.

Full background, decisions, and open questions: `docs/brief.md`. Read it at the start of any new planning discussion.

## About me / how to work with me
- I'm Isaac, a mechanical engineer in HVAC sales, comfortable with Python/JS, new to geospatial data.
- Explain the *why* before the *how*. Go step by step and keep steps small.
- Before writing a new script, tell me what it will do and what I should expect to see when I run it.
- After a step, tell me how to verify it worked.
- Don't jump ahead to later mini-projects unless I ask.

## Project structure
Six mini-projects, each shareable on its own:
1. Street data (done; see `reference/project1/`)
2. Permit data (done; see `docs/PROJECT_2_NOTES.md`)
3. Crane pricing (current)
4. Data synthesis and friction score
5. Interactive map
6. Cartogram

## Folder layout
- `data/raw/`: downloaded source files, never edited. Large files are gitignored.
- `data/processed/`: cleaned outputs from scripts
- `src/`: reusable Python modules
- `notebooks/`: exploration (optional)
- `outputs/`: charts and figures
- `docs/`: brief, per-project notes (`PROJECT_N_NOTES.md`), design specs in `docs/superpowers/specs/`
- `scripts/`: numbered pipeline scripts, run in order (`01_download.py`, `02_...`)
- `tests/`: pytest unit tests for `src/`
- `reference/`: the previous attempt. It is for ideas only. Don't import from it or edit it.

## Environment
- Use the project virtual environment in `.venv` (Python 3.14). Always run with `.venv/bin/python` or with the venv activated, never with the system `/usr/bin/python3`.
- Dependencies go in `requirements.txt`.
- Download data as CSV directly rather than reading from the API URL in pandas, which hit SSL errors on this Mac.

## Data gotchas already learned
- Centerline: group boroughs by `Borough Code` (1–5), not `Borough Indicator` (mostly empty).
- SSL errors hit Python's `urllib` too, not only pandas (`CERTIFICATE_VERIFY_FAILED`). Download with `curl` for now (`src/download.py` does this). Likely permanent fix: run `/Applications/Python 3.14/Install Certificates.command` once (not yet tried). `pip` in `.venv` works fine.
- DOT permits: use the `wkt` column (EPSG:2263, feet). `locationgeometry` is a binary blob.
- Read DOT CSVs with `dtype=str`. `applicationtrackingid` has 16 digits and becomes a wrong float otherwise.
- DOT application types: New, Renew, Reissue, Amend and Reissue.
- NTA boundaries run down street centerlines, like permit points. Points in park NTAs (`ntatype` 9) are moved to the nearest non-park NTA within 100 ft (`reassign_park_edges`); about 11% of points still sit on a boundary between two regular NTAs.
- Centerline street names: use `Street Name Label` and run it through `normalize_street_name`, same as permit names.
- `specificstipulations` custom text is on nearly every crane permit, so it does not separate neighborhoods.

## Permit data sources (spike, 2026-09-25)
DOT street crane permits are a better fit than general DOB permits: each record is a crane placed on a street. Project 2 is done (design: `docs/superpowers/specs/2026-09-25-project2-permit-data-design.md`). Pipeline: run `scripts/01_download.py` to `05_visualize.py` in order. Results: `docs/PROJECT_2_NOTES.md`.
- `tqtj-sjs8` Street Construction Permits (2022–present) and `c9sj-fmsg` (2013–2021, actually goes back to 1991). Same columns; stack them. Filter `permittypedesc = 'PLACE CRANE OR SHOVEL ON STREET'`. About 16.7k crane permits in the new set (77% have `locationgeometry`), about 148k in the old set (99% have geometry). No NTA column, so neighborhoods need a spatial join.
- `hcv3-zacv` Cranes: crane type per permit (mobile, crawler, tower). Joins on `permitnumber` to either permit dataset.
- No explicit application date. The first 8 digits of `applicationtrackingid` are read as one (YYYYMMDD). This passed all checks on 2026-09-26 (100% parse, 100% on or before issue date, median gap 3 days), but DOT's data dictionary does not document it, so it stays an inference.
- `specificstipulations` is free text with permit conditions (flaggers, work hours, bike lanes). Possible friction signal.
- Backup: `w9ak-ipjd` DOB NOW Build Job Filings. Has `filing_date`, `approved_date` (87% filled) and `nta` (99.7% filled), but covers all building jobs, not cranes.

## Conventions
- Scripts are split into load → clean → analyze → visualize.
- Every mini-project ends with `docs/PROJECT_N_NOTES.md`, which covers the findings, data quality issues, and next questions.
- Commit to git after each working step with a clear message.
- Update this file when we make a decision that future sessions should know about.
