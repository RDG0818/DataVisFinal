# IPEDS admissions backbone: schema and provenance

`data/ipeds_admissions_panel.csv` contains one row for every **reported** `UNITID × Fall year` in NCES Admissions (ADM), 2014–2024. It includes all ADM reporters, regardless of institution type. NCES restricts ADM reporting to institutions without open admissions; the file is **not a census of all U.S. colleges**. `cohort_year` is the fall entering cohort, not the publication year. ADM began as a separate component in 2014–15. All 22 source tables are official NCES downloads with exact URLs, extraction member, release type, and SHA-256 in `validation/ipeds_v2_sources.csv`. The 11 official NCES annual Access documentation workbooks used to decode ADMCON7 are hashed in `validation/ipeds_v2_codebook_sources.csv`.

The companion `data/institutions.csv` has one row per unique UNITID in the panel. It uses the latest *matching* HD row and records `metadata_year`. Names, control, state, Carnegie codes, and coordinates in the main panel always come from **HD of the same year**; they are not backfilled from 2024.

## Main fields

| Column | Meaning | Source / calculation |
| --- | --- | --- |
| `unitid`, `cohort_year` | NCES institution key and entering fall | `UNITID`, source table year |
| `institution_name`, `city`, `state` | Contemporary school identity | same-year `HD*.INSTNM`, `CITY`, `STABBR` |
| `control_code`, `control_label` | 1 public, 2 private nonprofit, 3 private for-profit | same-year `HD*.CONTROL` |
| `sector_code`, `institution_level_code`, `locale_code` | NCES categories; original codes retained | same-year `HD*.SECTOR`, `ICLEVEL`, `LOCALE` |
| `carnegie_*_code` | Available classification vintage only; blank means unavailable | same-year HD `CARNEGIE`/`C00CARNEGIE`, `CCBASIC`, `C15BASIC`, `C18BASIC`, `C21BASIC`, `CARNEGIEIC` |
| `longitude`, `latitude` | Coordinates as published that year | same-year `LONGITUD`, `LATITUDE`; negative special codes blanked |
| `applicants`, `admitted`, `enrolled` | First-time degree/certificate-seeking students, full plus part time | `APPLCN`, `ADMSSN`, `ENRLT` |
| `admit_rate`, `yield_rate` | Fractions **0–1**, respectively `admitted/applicants`, `enrolled/admitted` | calculated only if denominator positive |
| `sat_submit_count`, `act_submit_count` | Enrolled students whose test score was submitted | `SATNUM`, `ACTNUM` |
| `sat_submit_pct`, `act_submit_pct` | Percent of enrolled students submitting each exam, **0–100** | `SATPCT`, `ACTPCT`, no sum-to-100 assumption |
| `sat_reading_p25/p50/p75`, `sat_math_p25/p50/p75` | Reported exam-score percentiles | `SATVR*`, `SATMT*`; median appears only when NCES collected it |
| `act_composite_p25/p50/p75` | ACT composite percentiles | `ACTCM*`; median appears only when collected |
| `test_policy_code`, `test_policy_label`, `test_policy_era` | SAT/ACT admission consideration, original code plus exact year-specific NCES value label | `ADMCON7`; official annual Access `valueSets` sheet |
| `test_policy_codebook_url`, `test_policy_codebook_sha256` | Exact official workbook used for this row's policy label | Annual NCES Access documentation |
| `*_men`, `*_women`, `*_another_gender`, `*_gender_unknown` | Published breakdowns where available | corresponding ADM suffixes `M`, `W`, `AN`, `UN`; missing breakdown is not zero |
| `ipeds_status_flags_json` | All original nonempty `X*` flags, such as revised/imputed/reported statuses | verbatim keys and values from ADM CSV |
| `special_value_codes_json` | Any negative source codes or unexpected nonnumeric cell values | verbatim source key and value; affected numeric column blank |
| `adm_release`, `adm_source_url`, `hd_source_url`, `has_matching_hd` | Row provenance and same-year HD join state | release records and join |

Every transformed ADM and selected HD variable maps to its exact NCES column and years of availability in `validation/ipeds_variable_mapping.csv`. Other available score, enrollment, and consideration fields are preserved with readable names in the panel.

## Changes that affect longitudinal analysis

- **2014–2016 SAT reading** is *Critical Reading* on the old score version. **2017 onward** is Evidence-Based Reading and Writing on the new SAT version, with NCES instructions to concord old scores. Do not interpret a jump over 2016–2017 as a clean change in applicant quality. [NCES archived SAT change](https://nces.ed.gov/ipeds/report-your-data/archived-changes/2017-18).
- **ADMCON7 policy codes change in 2022**, established directly from the NCES Access documentation workbooks: 2014–2015 uses 1 Required, 2 Recommended, 3 Neither required nor recommended, 4 Do not know; 2016–2021 adds 5 Considered but not required and no longer has code 4. In 2022–2024 the options are 1 Required to be considered for admission, 5 Not required but considered if submitted (Test Optional), 3 Not considered even if submitted (Test Blind). The same numeric code 3 has a different meaning before and after 2022. Do not trend it as a stable policy. Exact code/value labels, workbook URLs, SHA-256 hashes, and `valueSets` worksheet row references are in `validation/ipeds_v2_policy_codes.csv`; the [NCES Access documentation page](https://nces.ed.gov/Ipeds/use-the-data/download-access-database) describes these metadata workbooks.
- Percent of enrolled students submitting SAT and ACT is measured separately; a student may submit both, so the two percentages may sum beyond 100. Scores describe *score-submitters*, not all enrolled students.
- NCES says ADM only covers institutions without open admissions. A row missing from a year does not establish closure or zero applicants. Same-year differences against Common Data Set observations are preserved as independent official reports. [NCES ADM methodology](https://nces.ed.gov/ipeds/survey-components/ipeds-survey-methodology).
- `ADM2024`/`HD2024` come from the official **2024–25 Provisional Access** release; 2014–2023 complete data files use final/revised releases when present. Provisional data have passed NCES quality control, but later final release may revise them. [NCES release explanation](https://nces.ed.gov/Ipeds/use-the-data/download-access-database).

## Validation

`validation/ipeds_v2_summary.json` gives coverage and error counts. `validation/ipeds_v2_year_coverage.csv` lists every year. `validation/ipeds_v2_issues.csv` records numeric exceptions. The build requires all 22 official file hashes to match acquisition records and all 11 official codebook hashes to match retrieval records; it also checks unique UNITID within each year's ADM and HD, same-year HD joins, nonnegative counts, applicants ≥ admits ≥ enrolled, percentage ranges, score ranges, and percentile ordering. It does not edit source data to pass a check. Rebuild with `python3 scripts/v2_ipeds/verify_codebooks.py` followed by `python3 scripts/v2_ipeds/build_ipeds.py` from the project root; only Python's standard library is needed.
