# DataVisFinal

## Phase 1: Project Definition

### General Research Question
How did first-year college admissions in the US change from 2014 to 2024?

### Specific Research Questions
1. Did first-year enrollment decline start before 2025, and which states, regions, and school types were hit first?
2. How did Covid (2019 to 2021) change applicants, admit rate, and yield, and did selective and open-access schools differ?
3. Did the shift away from SAT/ACT requirements change applications, admit rates, yield, and submitted scores?

### Intended Audience
- Primary: Higher-ed administrators, admissions staff, and education policymakers who plan around enrollment trends.
- Secondary: Informed general public (students, parents, counselors).
- Constraints: Non-technical readers, so plain labels, one message per figure, and no statistical jargon. Colorblind-safe palette, readable static figures (no interaction needed).

### Data
Kaggle: US College Admissions Panel (IPEDS + CDS), 2014-2024, 2,634 institutions, in `dataset/`. Use a fixed panel of schools that report every year. 2024 is provisional.

## Phase 2: Design and Data Prep

### Planned Visualizations
1. Enrollment change map by state (Q1)
2. Indexed enrollment lines by control and region (Q1)
3. Covid slope chart by selectivity tier (Q2)
4. Test submission rate by policy group (Q3)
5. Test-optional vs test-required outcomes (Q3)
6. ACT percentile shift (Q3, optional)

Design rules and figure specifics are in `CLAUDE.md`.

### Data cleaning
Code is in `clean_data.ipynb`. Setup:
```bash
python -m venv .venv
source .venv/bin/activate
pip install jupyter pandas matplotlib plotly kaleido
jupyter lab
```

The notebook does this, in order:
1. Load the columns we need from the panel.
2. Inspect years, control labels, test policy labels, and missing values.
3. Keep the 50 states and DC, and add Census region.
4. Drop impossible rows (admitted > applicants, enrolled > admitted, zero counts) and recompute admit and yield rates.
5. Add selectivity tier (2019 admit rate), test policy group (2019 vs 2022), and a score submission measure.
6. Build a fixed set of schools per figure and aggregate.
7. Check sizes and save tables to `clean/`.

Known limits to mention in the paper:
- The panel only has schools that report to IPEDS admissions. Open-admission schools are mostly missing, so the top tier in figure 3 is "least selective reporters", not open-access.
- "Enrolled" is first-time students only, not total enrollment.
- 2024 is provisional. Small states have few schools, so check `n_schools` before reading the map.

---
Push commands:
```bash
git add .
git commit -m "your commit message"
git push
```
