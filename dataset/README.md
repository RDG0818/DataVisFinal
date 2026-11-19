How did applications, admission rates and enrollment yield change over a decade—and what do waitlists and student profiles add to that picture? This dataset connects **every published NCES IPEDS ADM report from 2014–2024** with a carefully sourced Common Data Set enrichment layer. Build national or institution-level trends from the IPEDS backbone, then drill into CDS-only detail without losing denominators, document pages or disagreements.

**2,634 institutions · 22,531 observed institution-years · 11 entering-fall cohorts**  
CDS enhancement: **61 colleges and universities · 127 school-years · 1,473 numeric observations**. 46 institutions have both 2023 and 2024 CDS coverage. Actual field coverage is in the validation files; the CDS layer also preserves previously verified 2019–2025 observations.

### Three analysis entry points

1. **The admissions decade:** pair institutions over time; compare application growth, admission-rate changes and public/private nonprofit yield.
2. **The score-submission shift:** track SAT/ACT submission shares in a fixed reporting cohort; inspect annual policy definitions and missingness.
3. **Beyond IPEDS:** use CDS waitlists, GPA, class rank and selected need-based aid; trace each observation to the source table.

### Read it in five lines
```python
import pandas as pd
from pathlib import Path
root = next(Path('/kaggle/input').rglob('ipeds_admissions_panel.csv')).parent
panel = pd.read_csv(root / 'ipeds_admissions_panel.csv')
panel.query('cohort_year == 2024').sort_values('applicants', ascending=False).head()
```

### Files and principal fields

| Table | Key fields | Use |
|---|---|---|
| `ipeds_admissions_panel.csv` | `unitid`, `cohort_year`, `applicants`, `admitted`, `enrolled`, gender counts | Every ADM reporting institution-year, with derived admission and yield rates |
| Same IPEDS table | SAT/ACT 25th/75th scores, submission percentages, annual policy labels, NCES flags | Scores describe submitters; missing is never zero |
| Same IPEDS table / `institutions.csv` | School name, state, historical control, Carnegie classifications, coordinates | Historical HD in panel; explicitly dated latest profiles in institutions |
| `cds_enrichment_long.csv` | `metric`, `population`, `gender`, `residency`, `value`, `source_url`, `page` | Authoritative field-level CDS provenance |
| `cds_enrichment_wide.csv` | `unitid`, `cohort_year`, metric columns, `field_provenance` | Convenient exploration with exact provenance |
| `sources.csv`, `ipeds_variable_mapping.csv` | Official URLs, source hashes/release status; raw variable names | Audit and original-name lookup |
| `DATA_DICTIONARY.md`, `validation.zip`, `reproducibility.zip` | Definitions, coverage, checks, retained discrepancies, build code | Reproducible review |

### Boundaries that matter

This is an **unbalanced institutional panel** of ADM reporters, not all colleges or unique applicants. Open-admission institutions outside ADM are not added. A stable UNITID may mask changing campus scope. Use same-year HD attributes for historical comparisons, and check denominators before calculating rates. The 2024 release is provisional. SAT definitions and policy categories change during the decade; raw mappings, missing codes and NCES flags are retained. SAT and ACT submitter groups overlap. Score percentiles are conditional on submitters; composite percentiles are never synthesized by adding section percentiles. GPA scales are not automatically comparable. Aid means apply to recipients.

CDS and IPEDS can report different populations or revisions. **Both original values remain available**; no interpolation, zero filling or cross-source substitution is used. Numerical rule findings and source comparisons are preserved in `validation.zip`.

### Sources and license

IPEDS: [NCES official downloads](https://nces.ed.gov/ipeds/use-the-data), ADM and same-year HD, 2014–2024. Federal IPEDS data are **public domain**; see [Department of Education copyright guidance](https://www.ed.gov/about/contact-us/faqs). CDS: official university publications, with exact URLs and PDF pages/worksheet locations in the long table and source register. Original university documents retain their rights and are not bundled. Compilation, original code and documentation: **CC BY 4.0**. Please attribute yangkuangou and the source institutions.

The [companion notebook](https://www.kaggle.com/code/yangkuangou/a-decade-of-us-college-admissions-ipeds-cds) provides eight reproducible figures with data-derived captions.
