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
Setup:
```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib plotly kaleido
mkdir clean figures
```

1. Load only the columns we need.
```python
import pandas as pd

cols = ["unitid", "cohort_year", "institution_name", "state", "control_label",
        "applicants", "admitted", "enrolled", "sat_submit_pct", "act_submit_pct",
        "act_composite_p25", "act_composite_p50", "act_composite_p75",
        "test_policy_label"]
panel = pd.read_csv("dataset/ipeds_admissions_panel.csv", usecols=cols)
```

2. Look at it before changing anything. Check the exact `test_policy_label` strings, since step 5 depends on them.
```python
panel.groupby("cohort_year")["unitid"].nunique()
panel["control_label"].value_counts()
panel["test_policy_label"].value_counts(dropna=False)
panel[["applicants", "admitted", "enrolled"]].isna().mean()
```

3. Keep the 50 states and DC, and add Census region (drops territories).
```python
regions = {
    "Northeast": "CT ME MA NH RI VT NJ NY PA",
    "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
    "South": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
    "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
}
state_to_region = {s: r for r, v in regions.items() for s in v.split()}
panel["region"] = panel["state"].map(state_to_region)
panel = panel.dropna(subset=["region"])
```

4. Drop impossible rows and recompute the rates ourselves, so they match the counts we sum later. Blanks are left blank, never filled with zero.
```python
bad = ((panel.admitted > panel.applicants) | (panel.enrolled > panel.admitted)
       | (panel.applicants == 0) | (panel.admitted == 0))
panel = panel[~bad].copy()
panel["admit_rate"] = panel["admitted"] / panel["applicants"]
panel["yield_rate"] = panel["enrolled"] / panel["admitted"]
```

5. Add the groups we need.
```python
# selectivity tier from 2019 admit rate
base = panel[panel.cohort_year == 2019].set_index("unitid")["admit_rate"]
tier = pd.cut(base, [0, .25, .5, .75, 1], include_lowest=True,
              labels=["Under 25%", "25-50%", "50-75%", "Over 75%"])
panel["tier"] = panel["unitid"].map(tier)

# test policy group: required in 2019, then optional or still required in 2022
pol = panel.set_index(["unitid", "cohort_year"])["test_policy_label"].unstack()
req19 = pol[2019] == "Required"
group = pd.Series(pd.NA, index=pol.index, dtype="object")
group[req19 & (pol[2022] == "Required")] = "Stayed required"
group[req19 & pol[2022].notna() & (pol[2022] != "Required")] = "Went optional"
panel["policy_group"] = panel["unitid"].map(group)

# SAT and ACT takers overlap, so the max is a lower bound on "submitted any score"
panel["test_submit_pct"] = panel[["sat_submit_pct", "act_submit_pct"]].max(axis=1)
```

6. Build a fixed set of schools for each figure (only schools with data in every year), then aggregate. Rates are sums of counts divided, not averages of school rates.
```python
def fixed_panel(df, cols, n_years=11):
    d = df.dropna(subset=cols)
    n = d.groupby("unitid")["cohort_year"].nunique()
    return d[d["unitid"].isin(n[n == n_years].index)]

def index_to(df, by, value, base):
    t = df.groupby([by, "cohort_year"])[value].sum().unstack("cohort_year")
    return t.div(t[base], axis=0) * 100

# figures 1 and 2
enr = fixed_panel(panel, ["enrolled"])
st = enr.groupby(["state", "cohort_year"])["enrolled"].sum().unstack()
map_df = pd.DataFrame({
    "2014-2019": (st[2019] / st[2014] - 1) * 100,
    "2019-2024": (st[2024] / st[2019] - 1) * 100,
    "n_schools": enr.groupby("state")["unitid"].nunique(),
})
idx_control = index_to(enr, "control_label", "enrolled", 2014)
idx_region = index_to(enr, "region", "enrolled", 2014)

# figures 3 and 5
cov = fixed_panel(panel, ["applicants", "admitted", "enrolled"])
def rates(df, by):
    a = df.groupby([by, "cohort_year"], observed=True)[["applicants", "admitted", "enrolled"]].sum()
    a["admit_rate"] = a["admitted"] / a["applicants"]
    a["yield_rate"] = a["enrolled"] / a["admitted"]
    return a
by_tier = rates(cov, "tier")
by_policy = rates(cov.dropna(subset=["policy_group"]), "policy_group")

# figure 4
tst = fixed_panel(panel.dropna(subset=["policy_group"]), ["test_submit_pct"])
submit = tst.groupby(["policy_group", "cohort_year"])["test_submit_pct"].median().unstack()

# figure 6
act = fixed_panel(panel.dropna(subset=["policy_group"]), ["act_composite_p25", "act_composite_p75"])
act_med = act.groupby(["policy_group", "cohort_year"])[["act_composite_p25", "act_composite_p75"]].median()
```

7. Check sizes, then save. If a group or tier has only a handful of schools, merge tiers or say so in the caption.
```python
for name, d in [("enr", enr), ("cov", cov), ("tst", tst), ("act", act)]:
    print(name, d["unitid"].nunique())
print(cov.drop_duplicates("unitid")["tier"].value_counts())
print(cov.drop_duplicates("unitid")["policy_group"].value_counts())
print(map_df["n_schools"].describe())

map_df.to_csv("clean/map_df.csv")
for name, t in [("idx_control", idx_control), ("idx_region", idx_region), ("by_tier", by_tier),
                ("by_policy", by_policy), ("submit", submit), ("act_med", act_med)]:
    t.to_csv(f"clean/{name}.csv")
```

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
