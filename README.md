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
Kaggle: US College Admissions Panel (IPEDS + CDS), 2014-2024, 2,634 institutions, in `dataset/`. 2024 is provisional.

## Phase 2: Design and Data Prep

### Planned Visualizations
- [x] Covid enrollment map by state (Q2)

More figures will be added one at a time. Design rules and figure specifics are in `CLAUDE.md`.

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
2. Inspect years and missing values.
3. Keep the 50 states and DC.
4. Drop impossible rows (admitted > applicants, enrolled > admitted, zero counts).
5. Build the Covid table: % change in first-year enrollment by state, 2019 to 2020, using schools that report in both years. Saved to `clean/map_covid.csv`.

The map is drawn by `covid_map.py`, which reads `clean/map_covid.csv` and saves `figures/fig1_covid_map.png`. Run it from the repo root after the notebook:
```bash
python covid_map.py
```

---
Push commands:
```bash
git add .
git commit -m "your commit message"
git push
```
