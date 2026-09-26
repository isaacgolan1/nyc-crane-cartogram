# Project 2: Crane Permit Friction in Manhattan

*Part of the NYC Crane Logistics Cartogram. Data downloaded 2026-09-26.*

## Question

How hard does New York City make it to put a crane on the street, neighborhood by neighborhood?

Placing a mobile crane on a city street requires a NYC Department of Transportation (DOT) permit of type "Place Crane or Shovel on Street." Each permit is one crane occupying one block for a set number of days. That makes DOT permits a direct record of crane deployment. The original plan used Department of Buildings (DOB) job filings instead, but those cover all building work and measure building bureaucracy, not crane logistics.

This project produces two separate measures of permit friction for each Manhattan neighborhood:

1. **Lead time:** how long DOT takes to issue a new crane permit.
2. **Stipulation burden:** how many site-specific conditions DOT attaches to the permit.

They stay separate here. Project 4 combines them with crane cost and street access into one friction score.

## Data

| Dataset | NYC Open Data ID | Used for |
|---|---|---|
| Street Construction Permits (2022–Present) | `tqtj-sjs8` | 16,508 crane permits citywide, issued 2022-01-03 to 2026-09-25 |
| Street Construction Permits – Stipulations (2020–Present) | `gsgx-6efw` | 298,901 stipulation rows for those permits |
| Street Construction Permits – Cranes | `hcv3-zacv` | Crane type per permit (downloaded, not analyzed yet) |
| 2020 Neighborhood Tabulation Areas | `9nt8-h7nd` | 262 neighborhood boundaries |
| NYC Street Centerline | local file from Project 1 | Locating permits that have no map geometry |

All boroughs are downloaded and cleaned. Metrics are computed for Manhattan only (7,666 permits), with the borough list kept as a single setting so other boroughs can be added later.

## Method

**Pipeline.** Five scripts, run in order: `scripts/01_download.py` to `scripts/05_visualize.py`. Reusable logic lives in `src/` and has 61 unit tests.

**Location.**
- 77% of permits carry DOT's own line geometry. Each permit's point is the midpoint of that line.
- The other permits are located from their street description ("East 56 Street between 1 Avenue and 2 Avenue"). Street names are normalized on both sides ("EAST 55 STREET" and "E 55 ST" both become `E 55 ST`). The script finds where the street crosses each cross street in the city centerline and takes the point halfway between. If only one cross street matches, it uses that intersection.
- Each point is assigned to the neighborhood (NTA) that contains it.
- **Park edges.** Neighborhood boundaries run down street centerlines, and so do permit points. A crane on Fifth Avenue lifting onto an Upper East Side building therefore landed in "Central Park." Points that fall in a park neighborhood now move to the nearest non-park neighborhood within 100 feet. Points deeper inside a park stay there.

**Lead time.**
- DOT publishes no application date. The first 8 digits of `applicationtrackingid` read as a date (YYYYMMDD). Before relying on that reading, a check script tested it: 100% of IDs parse as a real date, 100% of those dates fall on or before the issue date, and the median gap is 3 days. DOT's data dictionary describes the field only as "System generated ID for the application", so the date reading is an inference, but a well-supported one.
- Lead time = issue date minus that application date, for **New** permits only. Renewals and reissues are issued faster (median 1–3 days) because the site was already reviewed, and would hide the real first-approval wait.

**Stipulation burden.**
- DOT attaches coded conditions to each permit, such as flaggers, weekend-only work, road-closure notices and temporary bike lanes. There are 2,012 distinct codes citywide.
- Codes on more than 90% of crane permits are treated as boilerplate and ignored, because they add the same amount everywhere. The cutoff is computed from all citywide permits, so adding a borough later does not change which codes count. Nine codes are boilerplate (`012`, `038`, `066`, `091`, `103`, `NOISE1`, `ODV`, `SCHOOL`, `TMC001`); the next most common code is on 82%, well below the cutoff.
- Stipulation burden = number of non-boilerplate codes on a permit, across all application types.

**Neighborhood values.** Medians, not means, so a few extreme permits don't dominate. A neighborhood needs at least 20 permits for a metric; below that the metric is left blank and the neighborhood is flagged `insufficient_data`.

## Data quality funnel (Manhattan)

| Step | Permits |
|---|---|
| Crane permits issued 2022-01-01 onward | 7,666 |
| Duplicate permit numbers | 0 |
| Located from DOT geometry | 5,904 |
| Located by centerline geocoding | 1,729 |
| Could not be located (`no_location`) | 33 (0.4%) |
| Point in another borough (`borough_mismatch`, Marble Hill) | 2 |
| Point outside every neighborhood (`outside_nta`, Brooklyn Bridge) | 1 |
| **Usable for metrics** | **7,630** |
| Moved from a park edge to the neighboring NTA | 226 |
| New permits with a usable lead time | 5,108 (0 excluded as emergency, unparsed or implausible) |

Citywide, 201 permits (1.2%) could not be located. The unmatched street descriptions are listed in `data/processed/geocode_unmatched.csv`; common causes are highway and tunnel-approach names ("JOE DIMAGGIO HIGHWAY", "LINCOLN TNNL APPROACH") and placeholder cross streets ("DEAD END", "BEND").

The Marble Hill result is correct, not an error: Marble Hill is legally part of Manhattan but lies on the Bronx side of the river, and the city's neighborhood map places it in a Bronx neighborhood.

## Findings

Full table: `data/processed/permit_friction_by_nta.csv` (38 neighborhoods, 31 with both metrics).

**Stipulation burden is the strong signal.** Median distinctive stipulations per permit:

- Highest: Midtown-Times Square (13), then Midtown South-Flatiron-Union Square, SoHo-Little Italy-Hudson Square, Greenwich Village, East Midtown-Turtle Bay, Murray Hill-Kips Bay, Gramercy and Chinatown-Two Bridges (11 each).
- Lowest: Washington Heights (South) (7), with most of Upper Manhattan, the Lower East Side and Tribeca at 8.

A crane permit in Midtown carries almost twice as many site-specific conditions as one in Washington Heights. That fits what the codes describe: more traffic lanes to keep open, more pedestrian routing, more bike lanes and more event embargoes.

**Lead time varies little.** The median New permit is issued 5 days after application (middle half: 3–7 days).

- Highest: Upper East Side-Lenox Hill-Roosevelt Island and Upper West Side-Lincoln Square (7 days), with ten more neighborhoods, including Midtown, Chelsea-Hudson Yards and the Financial District, at 6.
- Lowest: Upper West Side-Manhattan Valley (2 days), with Washington Heights, Harlem (North) and Morningside Heights at 3.
- The distribution has two peaks, around 2 days and around 7 days. This may reflect two review tracks, for example routine sites versus sites needing coordination.

**Most common distinctive conditions** (share of Manhattan crane permits): reopen the full roadway when unattended (`078`, 85%), reopen the full sidewalk when unattended (`016`, 83%), road-closure notice to police, fire, EMS and neighbors 7 days ahead (`022`, 46%), weekend-only work (`074`, 28%), temporary bike lane (`BIKE01`, 15%), weekday 9AM–3PM only (`087`, 9%).

**Custom text is universal.** Nearly every Manhattan crane permit has site-specific free text from a DOT reviewer (`pct_custom_text` is 96–100% in every neighborhood), so it does not separate neighborhoods.

**Embargo codes** (event and holiday work bans, `SE…`) make up 12.1% of distinctive code uses.

Charts:

- `outputs/p2_lead_time_distribution.png`
- `outputs/p2_lead_time_by_nta.png`
- `outputs/p2_stipulations_by_nta.png`
- `outputs/p2_top_distinctive_codes.png`

## Limitations

- **Application date is inferred.** The tracking-ID date passed every check, but DOT does not document it. The ID is probably created when an application is started, so lead time may include some of the applicant's drafting time.
- **Boundary points.** About 11% of Manhattan permit points sit within 25 feet of a neighborhood boundary, because both run down street centerlines. For these, which side a permit lands on is effectively arbitrary. Park edges are corrected; boundaries between two regular neighborhoods are not.
- **Ties.** Medians are whole numbers, so many neighborhoods tie (nine at 8 stipulations). The top-10 and bottom-10 charts break ties by permit count, not by a real difference.
- **Embargo codes mix time and place.** A permit carries an embargo code partly because of *when* it runs, not only where.
- **The 90% boilerplate cutoff is a shortcut.** A code on 50% of permits spread evenly across neighborhoods also tells nothing apart. A precise test would check whether each code's rate varies by neighborhood.
- **Pre-2022 data is unused.** The 2013–2021 dataset (`c9sj-fmsg`, about 148,000 crane permits back to 1991) could test whether these patterns hold over time.

## Next questions

1. **Cost buckets for stipulations.** Group the codes by the kind of cost they create (lost work hours, space limits, extra staff, advance notice, agency coordination), ideally labeled with input from contractors. This would say not just "more conditions" but "more expensive conditions."
2. **Why two lead-time peaks?** Check whether the 2-day and 7-day groups differ by crane type, road-closure codes or permit length.
3. **Renewal chains.** Permits link to the one before them (`previouspermitnumber`). Long chains could mean DOT grants short windows in some neighborhoods, which is hidden friction.
4. **Other boroughs.** The data is already downloaded and cleaned; change `BOROUGHS` in `src/config.py`.
5. **For Project 4:** stipulation burden differentiates neighborhoods far more than lead time does. The combined friction score should weight them accordingly, or test both.
