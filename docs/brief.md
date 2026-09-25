# NYC Crane Cartogram Project — Handoff Brief

**Date**: September 25, 2026  
**Status**: Mini-Project 1 Complete (Street Data Exploration)  
**Next Phase**: Mini-Project 2 (Permit Data Analysis)

---

## Goal

Build a **data visualization portfolio project** that deforms NYC's geography based on crane deployment logistics costs/complexity instead of Euclidean distance. The final product is an interactive cartogram showing how "expensive" and "bureaucratically difficult" it is to deploy heavy equipment across NYC neighborhoods.

**Portfolio angle**: Demonstrates ability to synthesize multiple messy real-world data sources into a cohesive, insightful visualization. Targets data roles that need data synthesis, spatial analysis and full-stack visualization.

---

## Core Requirements

1. **Data Synthesis**: Combine 3+ independent data sources (street widths, permit timelines, crane costs) into one clean dataset
2. **Metrics Engineering**: Define a "logistics friction score" that weighs permit complexity + crane cost + street accessibility
3. **Visualization**: Create an interactive cartogram (deformed map) showing neighborhoods stretched/squeezed by friction
4. **Storytelling**: Annotated analysis explaining why certain neighborhoods are "farther" in logistics-space

---

## Project Structure: 6 Mini-Projects

Each mini-project is independent and shareable. They feed into a final integration layer.

### **Mini-Project 1: Street Data** ✅ COMPLETE
- **Goal**: Get comfortable with geographic data; establish baseline
- **Deliverables**: 
  - `load_street_data.py` — Load NYC centerline CSV (122,256 street segments)
  - `analyze_streets.py` — Calculate average street widths by borough
  - `visualize_streets.py` — Create bar charts (mean + median widths by borough)
  - `street_width_by_borough.png` & `street_width_median_by_borough.png`
  - `PROJECT_1_NOTES.md` — Document findings
- **Key Finding**: Manhattan/Bronx avg 35–36 ft; Queens/Staten Island avg 32 ft
- **Data Source**: NYC Open Data (Centerline_20260828.csv) — public, clean
- **Tools Used**: Pandas (data loading/analysis), Matplotlib (visualization)

### **Mini-Project 2: Permit Data** → NEXT
- **Goal**: Understand NYC DOB permit timelines; extract approval patterns by neighborhood
- **Planned Deliverables**:
  - Script to load + clean DOB permit dataset
  - Analysis of median approval times by borough/neighborhood/permit type
  - Visualization of permit approval distributions
  - Data quality assessment (missing values, outliers)
- **Data Source**: NYC Open Data (DOB permit records) — messy government data
- **Key Skills**: Data cleaning, handling weird date formats, dealing with missing values

### **Mini-Projects 3–4**: Crane Pricing + Data Synthesis
- Collect crane rental costs (via phone calls to companies + public sources)
- Merge all datasets by neighborhood
- Create initial "friction score"

### **Mini-Projects 5–6**: Visualization + Cartogram
- Interactive map with score visualization
- Cartogram deformation (final "wow" factor)

---

## Key Decisions & Why

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Start with geography?** | Yes (street data first) | Grounds the project in spatial thinking; builds comfort with geospatial data before complexity |
| **Local vs. Cloud** | VSCode local + Python | User has coding experience; local setup teaches environment management (Python versions, package management) |
| **Granularity** | Neighborhood-level (initially) | Simplifies data collection; matches permit records granularity; can drill down later |
| **Initial scope** | Manhattan-only MVP possible | Reduces data collection burden; tighter narrative (permits, cranes concentrated here) |
| **Cartogram algorithm** | TBD (deferred to project 6) | Focus on data quality first; rendering is secondary |

---

## Approaches Tried & Rejected

| Approach | Why Rejected |
|----------|-------------|
| Download street data via API (`read_json` on NYC portal URL) | SSL certificate errors on Mac; switched to direct CSV download instead |
| Use `Borough Indicator` column for borough grouping | Column mostly empty; switched to `Borough Code` (1–5) which is fully populated |
| Single combined script for all analysis | Inefficient; split into three files for clarity: load → analyze → visualize |

---

## Open Questions

1. **Permit data granularity**: Will DOB dataset have neighborhood-level approval times, or only borough-level? May need to aggregate differently.
2. **Crane cost variability**: How much do costs vary by crane type (mobile vs. tower)? By season? By day of week? Will need to scope data collection.
3. **Friction metric formula**: Is it a simple weighted sum (0.4×permit_time + 0.3×crane_cost + 0.3×street_width)? PCA-based? Multi-dimensional? Decision point for Mini-Project 4.
4. **Cartogram library**: Use `cartogram` Python library, D3.js, or custom geometry? Depends on interactivity needs.
5. **Temporal dimension**: Single snapshot (2024 average) or time-lapse animation showing seasonal variation?

---

## What I'd Do Differently Starting Over

1. **Validate permit data availability earlier**: Before committing to Mini-Project 2, confirm DOB has neighborhood-level approval time data. If not, pivot to precinct-level or create synthetic timeline estimates.
2. **Prototype the friction metric sooner**: Don't wait until project 4. By mid-project 2, have a rough formula ready so later data collection is purposeful (know what variables matter most).
3. **Sketch the final cartogram early**: A rough hand-drawn or digital sketch of what the deformed map should *look like* would guide data collection (which neighborhoods should "stretch"?).
4. **Interview construction people sooner**: Call 2–3 crane companies and contractors in project 1, not project 3. Their language and mental models inform the whole framing.
5. **Split permit data work into two sub-tasks**: (a) data loading/cleaning, (b) analysis/visualization. The cleaning is the hard part and deserves its own focused effort.

---

## Environment Setup Status

- ✅ Python 3.14 installed (`/usr/local/bin/python3`)
- ✅ VSCode configured with Python extension
- ✅ Pandas, Matplotlib installed (`pip3 install pandas matplotlib`)
- ⚠️ Note: Terminal sometimes defaults to wrong Python path (`/usr/bin/python3` vs. `/usr/local/bin/python3`). Set VSCode interpreter to `/usr/local/bin/python3` explicitly.

---

## Files in Project Folder

```
nyc-crane-project/
├── Centerline_20260828.csv          (input data — street widths)
├── load_street_data.py              (script: load CSV)
├── analyze_streets.py               (script: calculate averages)
├── visualize_streets.py             (script: make charts)
├── street_width_by_borough.png      (output: mean widths chart)
├── street_width_median_by_borough.png (output: median widths chart)
├── PROJECT_1_NOTES.md               (documentation)
└── HANDOFF_BRIEF.md                 (this file)
```

---

## Next Steps (For Claude Code Project)

1. **Start Mini-Project 2**: Download DOB permit dataset from NYC Open Data
2. **Explore**: What columns exist? How granular is the data? How many nulls?
3. **Clean**: Handle date formats, missing values, outliers
4. **Analyze**: Median approval times by borough/neighborhood/permit type
5. **Visualize**: Distribution charts, comparisons
6. **Document**: PROJECT_2_NOTES.md

---

## Context for New Session

- User: Isaac Golan
- Coding experience: Classroom + internships; comfortable with Python/JS; first time with geospatial data
- Learning style: Prefers step-by-step hand-holding with "explain like I'm 5" breakdowns; appreciates understanding *why* before doing
- Goal: Build shareable portfolio project that demonstrates data synthesis + visualization skills
