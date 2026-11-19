# DataVisFinal

## Phase 1: Project Definition

### General Research Question
How did first-year college admissions in the US change from 2014 to 2024, and what did Covid and test-optional policies do to applications, admit rates, and enrollment?

### Specific Research Questions
1. **Enrollment cliff:** Did first-year enrollment decline start before 2025, and which states, regions, and school types were hit first?
2. **Covid:** How did Covid (2019 to 2021) change applicants, admit rate, and yield, and did selective and open-access schools differ?
3. **Test-optional:** Did the shift away from SAT/ACT requirements change applications, admit rates, yield, and submitted scores?

### Intended Audience
- **Primary:** Higher-ed administrators, admissions staff, and education policymakers who plan around enrollment trends.
- **Secondary:** Informed general public (students, parents, counselors).
- **Constraints:** Non-technical readers, so plain labels, one message per figure, and no statistical jargon. Colorblind-safe palette, readable static figures (no interaction needed).

### Data
Kaggle: US College Admissions Panel (IPEDS + CDS), 2014-2024, 2,634 institutions, in `dataset/`. Use a fixed panel of schools that report every year. 2024 is provisional.

### Planned Visualizations
1. **Enrollment change map (Q1):** US state choropleth of % change in first-year enrollment, 2014-2019 vs 2019-2024.
2. **Indexed enrollment lines (Q1):** 2014 = 100, by control and Census region.
3. **Covid slope chart (Q2):** Applicants, admit rate, and yield, 2019 vs 2021, by selectivity tier.
4. **Test submission rate over time (Q3):** Median SAT/ACT submit rate by 2019 policy group, line at 2020.
5. **Test-optional vs test-required outcomes (Q3):** Applications, admit rate, and yield indexed to 2019 = 100.
6. **SAT percentile shift (Q3, optional):** Median 25th/75th percentile SAT by year for the same two groups.

---
Push commands:
```bash
git add .
git commit -m "your commit message"
git push
```
