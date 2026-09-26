# Project 2: Permit Data — Design

**Date:** 2026-09-25
**Status:** Approved in brainstorming, awaiting spec review
**Replaces:** the DOB-only plan in `docs/brief.md` (Mini-Project 2 section)

## Goal

Measure **permit friction** for placing a crane on the street, per NYC neighborhood, starting with Manhattan. Permit friction means "how hard does the city make it to put a crane here?"

Project 2 produces two separate neighborhood metrics. They are combined with crane cost and street access in Project 4, not here.

## Decisions

| Topic | Decision | Why |
|---|---|---|
| Core data | DOT street construction permits of type `PLACE CRANE OR SHOVEL ON STREET` | Each record is an actual crane occupying a street. DOB permits measure building bureaucracy, not crane deployment. |
| DOB NOW (`w9ak-ipjd`) | Not used, unless the tracking-ID check fails (see Lead time) | Keeps "permit friction" focused on cranes. |
| Years | 2022-01-01 to latest, from `tqtj-sjs8` only. The date range is a setting. | One data system, recent, and enough volume (about 7,700 Manhattan permits). Pre-2022 data is kept for later trend work. |
| Boroughs | Manhattan only for metrics. Borough list is a setting. All boroughs are downloaded and cleaned. | Manhattan-first MVP. Expanding later means one config edit. |
| Neighborhood unit | NTA 2020 boundaries (citywide file) | Official, covers all five boroughs, so nothing changes when expanding. |
| Metrics | Two separate metrics: lead time and stipulation burden | Different units (days vs count). Weighting happens once, in Project 4. |
| Permits without location (23%) | Geocode from street names against the centerline file. NYC Geoclient only if more than 5% stay unmatched. | Keeps nearly all data, avoids bias if missing locations cluster, reuses Project 1 data. |
| Application types | Lead time from `New` permits only. Stipulations from all types (New, Renew, Reissue, Amend and Reissue). | Renewals issue fast and would hide the real first-approval wait. Every permit's conditions apply to the work. |
| Thin neighborhoods | Minimum 20 permits per metric (setting). Below that, the metric is blank and the neighborhood is flagged `insufficient_data`. | A median from 3 permits is noise. Honest gray on the map beats a fake number. |
| Stipulation counting | Count only codes that tell neighborhoods apart (drop codes on more than 90% of crane permits), plus a flag for custom free text | Codes on every permit add the same amount everywhere and hide real differences. |
| Code structure | Script pipeline with shared modules in `src/` (Approach 1) | Matches project conventions. Modules carry into Projects 3–6. |

## Data sources

All data except the centerline comes from NYC Open Data's SODA API ("the API" in this spec). Each dataset has a URL of the form `https://data.cityofnewyork.us/resource/<id>.csv`, which accepts filters such as `$where` and `$limit`, so the server filters before sending.

| Dataset | ID | Use |
|---|---|---|
| Street Construction Permits (2022–Present) | `tqtj-sjs8` | Core permit records, filtered to crane type |
| Street Construction Permits – Cranes | `hcv3-zacv` | Crane type per permit. Downloaded for later; not analyzed in Project 2. |
| Street Construction Permits – Stipulations (2020–Present) | `gsgx-6efw` | One row per stipulation code per permit. 46.9M rows total, so download only rows for our crane permits, in batches of permit numbers. |
| 2020 Neighborhood Tabulation Areas (NTAs) | `9nt8-h7nd` | Neighborhood polygons for the spatial join |
| Centerline | already in `data/raw/Centerline_20260828.csv` | Geocoding permits that lack `locationgeometry` |

All downloads use `curl`, because Python's `urllib` hits `CERTIFICATE_VERIFY_FAILED` on this Mac.

## Architecture

```
src/
  config.py      boroughs, date range, thresholds (90% boilerplate cutoff, min 20 permits, 5% geocode fallback trigger)
  download.py    curl wrapper: filtered queries, paging, batching by permit number, retries, row-count check
  geo.py         street-name normalizer, centerline geocoding, NTA spatial join

scripts/ (run in order)
  01_download.py            → data/raw/
  02_verify_tracking_id.py  → prints pass/fail report
  03_clean.py               → data/processed/crane_permits_clean.csv
  04_analyze.py             → data/processed/permit_friction_by_nta.csv
  05_visualize.py           → outputs/

tests/
  test_*.py      pytest unit tests for pure functions in src/
```

Each stage saves its output to disk, so any stage can be rerun alone and any intermediate file can be opened and checked.

### Stage 1: Download

Four raw files, all boroughs, named with the download date (for example `dot_crane_permits_2026-09-25.csv`):

1. Crane permits from 2022 on (`tqtj-sjs8`, filtered to `permittypedesc = 'PLACE CRANE OR SHOVEL ON STREET'`)
2. Crane types (`hcv3-zacv`)
3. Stipulations for those permit numbers only (`gsgx-6efw`)
4. NTA 2020 boundaries

Raw files are never edited.

### Stage 2: Verify tracking-ID date

`applicationtrackingid` has no documentation. Its first 8 digits look like an application date (YYYYMMDD). The lead-time metric depends on this reading, so it is checked before anything is built on it.

First, look for the field in DOT's data dictionary. Then test the full dataset. The check **passes** only if all of these hold:

- The first 8 digits parse as a real date in 100% of rows.
- The application date is on or before `permitissuedate` in at least 99% of rows.
- The median gap is between 1 and 60 days.

The script prints the evidence either way. If the check fails, lead time is dropped and we decide on the DOB NOW fallback before continuing.

### Stage 3: Clean

1. Parse dates.
2. Check `permitnumber` uniqueness. Report duplicates and keep the latest `modifiedon`.
3. Use the `wkt` column where present (text geometry in EPSG:2263, feet). `locationgeometry` holds the same data as a binary blob and is not used.
4. For permits without it, geocode from `onstreetname` + `fromstreetname` / `tostreetname`:
   - Normalize street names (extra spaces, EAST→E, STREET→ST, AVENUE→AVE, number words). The same normalizer runs on centerline names, so both sides always agree.
   - Match the on-street and both cross streets to a centerline block and use the block's midpoint. If only one cross street matches, use that intersection.
   - Write unmatched permits to a file for inspection.
5. Spatial join each point to an NTA. NTA boundaries run down street centerlines, so a point that lands in a park NTA (`ntatype` 9) moves to the nearest non-park NTA within 100 ft. Example: a crane on Fifth Avenue lifting onto an Upper East Side building would otherwise count for Central Park. Points deeper inside a park stay there. (Added during implementation, 2026-09-26.)
6. Flag points outside every NTA, and points whose NTA borough differs from the permit's `boroughname`. Exclude both from metrics.

Output: `crane_permits_clean.csv`, one row per permit, with lat/lon, NTA, borough, and a location source column (`dot_geometry` or `centerline_geocode`). The file opens in Excel.

### Stage 4: Analyze

**Lead time** (per `New` permit):

- `application_date` = first 8 digits of `applicationtrackingid` (only if Stage 2 passes)
- `lead_time_days` = `permitissuedate` minus `application_date`, in days
- Excluded: emergency permits (`emergencyissuedate` not empty), negative gaps, gaps over 365 days. Each exclusion is counted and reported.

**Stipulation burden** (per permit, all application types):

- For each stipulation code, compute the share of crane permits carrying it. This uses **all citywide** crane permits in the date range, before location flags are applied, so adding a borough later does not change which codes count for Manhattan.
- `boilerplate` = codes on more than 90% of permits.
- `distinctive_stip_count` = number of non-boilerplate codes on the permit.
- `has_custom_text` = `specificstipulations` is not empty.

A sample of 495 recent Manhattan crane permits had 281 distinct codes and 19.5 per permit on average. Nine codes appeared on 100%: `012`, `038`, `066`, `091`, `103`, `NOISE1`, `ODV`, `SCHOOL`, `TMC001`.

Known caveat: embargo codes (`SE…` prefix, for example Summer Streets) depend on *when* a permit runs as well as *where*. They count like other codes for now. The notes report how much they contribute.

**Per neighborhood** (one row per NTA, medians not means):

| Column | Meaning |
|---|---|
| `nta_name`, `borough` | Neighborhood |
| `n_permits`, `n_new_permits` | Sample sizes |
| `median_lead_time_days` | Blank if fewer than 20 New permits |
| `median_distinctive_stips` | Blank if fewer than 20 permits |
| `pct_custom_text` | Share of permits with custom conditions |
| `insufficient_data` | True if either metric is blank |

Output: `permit_friction_by_nta.csv`.

### Stage 5: Visualize

Four charts in `outputs/`:

1. Lead-time distribution
2. Top and bottom 10 neighborhoods by median lead time
3. Top and bottom 10 neighborhoods by median distinctive stipulations
4. Most common distinctive stipulation codes

No maps. Maps are Project 5.

## Data quality and error handling

Nothing disappears silently. Every script prints a funnel: rows in, rows out, and the reason for each removal. The funnel goes into the Project 2 notes.

- **Paging:** the API caps rows per request, so `download.py` pages through results.
- **Row-count check:** after each download, compare our row count with the API's `count(*)`. A mismatch is an error.
- **Retries:** failed requests retry 3 times, then stop with a clear message.
- **Geocode fallback trigger:** if more than 5% of permits stay unmatched after centerline geocoding, add NYC Geoclient (needs a free API key).

## Testing

**Automated** (`pytest`, written before each function):

- Street-name normalizer: `"EAST   55 STREET"` → `"E 55 ST"`, plus about a dozen real messy examples.
- Tracking-ID parser: `"2026092200673116"` → 2026-09-22. Bad input returns blank, not a crash.
- Boilerplate finder: on a tiny made-up table, codes on more than 90% of permits are flagged.
- Neighborhood rollup: 19 permits gives a blank metric, 20 gives a number.

**Manual:**

- After `01`: row counts match the API.
- After `03`: pick 5 permits, look up the addresses on Google Maps, and confirm the assigned neighborhood.
- After `04`: sanity-check the ranking. Midtown and FiDi should rank high. If quiet residential areas rank highest, suspect a bug first.

## Deliverables

- `data/processed/crane_permits_clean.csv`
- `data/processed/permit_friction_by_nta.csv`
- Four charts in `outputs/`
- `docs/PROJECT_2_NOTES.md`: findings, data quality funnel, next questions
- `requirements.txt` (adds `geopandas`, `shapely`, `pytest`)
- `.venv` created (does not exist yet)
- CLAUDE.md updated with these decisions

## Out of scope

- Maps (Project 5)
- The combined friction score (Project 4)
- Grouping stipulation codes into cost buckets ("Option C": lost hours, space limits, extra staff, advance notice, coordination). Later upgrade; needs hand-labeling of 281 codes and pattern-grouping of embargo codes.
- A precise per-code test of "does this code's rate vary by neighborhood" (comes with Option C)
- Renewal chains (`previouspermitnumber`)
- Pre-2022 data (`c9sj-fmsg`)
- Metrics for boroughs other than Manhattan (their data is downloaded and cleaned)
- Crane type analysis
