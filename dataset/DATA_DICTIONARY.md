# US College Admissions Panel 2014–2024: IPEDS + CDS

## Tables, scope and joins

| File | Grain and purpose |
|---|---|
| `ipeds_admissions_panel.csv` | Every published ADM institution × entering-fall year, 2014–2024; same-year HD attributes |
| `institutions.csv` | One UNITID, most recent available same-source directory profile; snapshot year is explicit |
| `cds_enrichment_long.csv` | Exact metric × population × category observation; official source URL and page |
| `cds_enrichment_wide.csv` | Institution × actual cohort year; all populated fields carry JSON provenance |
| `sources.csv` | All used NCES tables and university documents, URLs, available hashes and release status |
| `ipeds_variable_mapping.csv` | Original IPEDS variables to readable names, annual availability and units |
| `validation.zip` | Row coverage, field coverage, rule findings, source and difference checks |
| `reproducibility.zip` | Acquisition/build code, frozen CDS observations and source manifests |

Join on `unitid` and `cohort_year`. The backbone covers all ADM reporters, including non-four-year institutions and US jurisdictions. It is not every institution in HD and is not a balanced panel. No missing institution-year is synthesized. A blank never means zero. Current institution profiles must not be substituted for historical control, names, classifications or locations in the panel. A stable UNITID does not guarantee a stable institutional footprint; mergers and branch reorganizations require further research.

Counts are institution reports, not national unique people. Derived admission rate = admitted/applicants and yield = enrolled/admitted, with positive denominators. Preserve source missingness and NCES imputation/status flags. The 2024 release is provisional; earlier acquired releases are labeled individually. No custom imputation or interpolation is performed.

CDS enrichment retains the accepted v1 observations from 2019–2025, with this round prioritizing 2023 and 2024. Its range is deliberately wider than the IPEDS title range. The two layers are not silently combined or overwritten; `validation/v2/consistency.csv` inside the archive records exact differences. Source scope can differ (for example, Columbia College/Engineering vs the UNITID, or Purdue campus reorganizations).

## Source rights

NCES IPEDS federal statistical data are public domain. [US Department of Education copyright guidance](https://www.ed.gov/about/contact-us/faqs) and the [official IPEDS download portal](https://nces.ed.gov/ipeds/use-the-data). Original compilation, documentation and code: CC BY 4.0, attribution to yangkuangou and source institutions. University CDS documents retain their own rights; original university PDFs are not bundled or relicensed. No endorsement is implied. Source URLs in `sources.csv` and the CDS long table identify the evidence for numeric observations.

## IPEDS definitions and annual variable mapping

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


## Explicit CDS source inconsistencies

Purdue 2024 has `admitted=30272` in the official printed total CDS-C!C42, while independently summing the gender categories (22551+16721) or residency categories (9091+25935+4246) gives 39272. `admitted_sum_of_reported_categories=39272` preserves that alternative as a separate derived metric. Default CDS rates use the reported `admitted`; the alternative is not substituted. The reporting footprint expands in 2024 to West Lafayette, Indianapolis and Polytechnic Statewide. Case Western 2024 reports ACT submission of 23% beside 269 submitters, whereas C1 enrolled is 1619; preserve the reported percentage and flag the unresolved denominator/version difference. See the source inconsistency table in validation.zip.

## CDS definitions (retained and renamed from v1)

# Data dictionary — US College Admissions CDS Panel

A source-preserving, unbalanced institution × entering-fall-cohort panel. The data are institutional descriptions, not estimates of an individual applicant's chance of admission. Blank means unavailable, uncollected, not applicable, or not yet verified; it never means zero.

## Files and keys

- `cds_enrichment_long.csv`: one numeric observation per `(unitid, cohort_year, section, metric, population, gender, residency)`. It is the authoritative table for field-level provenance.
- `cds_enrichment_wide.csv`: one row per `(unitid, cohort_year)`. Columns suffix a non-default population, gender, or residency with `__population_…`, `__gender_…`, or `__residency_…`. Empty expected metric columns are intentional.
- `sources.csv`: source documents actually used, source IDs, exact URLs, edition, acquisition details and SHA-256 where original bytes were obtainable. A web-viewed document may have no local PDF or hash; this is explicit in its notes. `cohort_years` lists every referenced year; `cohort_year` is empty when the same source contributes to multiple cohorts.
- `consistency.csv`: C1 totals compared with the same institution and fall year in official NCES IPEDS ADM. All differences are retained; CDS values are never changed to agree with IPEDS.
- `coverage.csv`, `metric_coverage.csv`, `issues.csv`, `summary.json`: actual coverage, missingness, rule findings and validation summary.

## Identifiers and provenance

| Column | Definition |
|---|---|
| `school` | Display name of reporting institution. Use `unitid` for joins. |
| `unitid` | NCES IPEDS institution identifier; not a rank or campus-system identifier. Reporting-footprint caveats remain relevant. |
| `cohort_year` | Entering fall year explicitly specified in the CDS question, 2019–2025. It is not the download year or high-school graduating class year. For B1, this is the fall census year. For first-year H2 aid, it is the beginning year of the actual aid academic year, even when that is a year earlier than the CDS edition; notes identify actual versus estimated aid. |
| `cds_edition` | Actual academic-year edition, e.g. `2024-2025`; never infer cohort solely from the filename. |
| `section` | CDS question/section label in the source edition; GPA labels can change across editions. |
| `metric` | Stable semantic metric name described below. |
| `population` | Denominator population. Default `first_time_first_year`; aid requires its own full-time population. |
| `gender` | Source category, normally `total`, `male`, `female`, `another_gender`, or `unknown`. Historical categories differ; unreported categories are not assumed zero. |
| `residency` | Source category, normally `all`, `in_state`, `out_of_state`, or `international`. Domestic nonresident and international are not interchangeable. |
| `value` | Numeric CDS value or explicitly documented sum of reported categories; no imputation, interpolation, or IPEDS replacement. |
| `unit` | `count`, `percent` (0–100, not 0–1), `score`, `gpa`, or `usd`. |
| `source_id` | Deterministic identifier of institution, edition and exact source URL, joinable to `sources.csv`. |
| `source_url` | Exact official source, including version-specific filename if applicable. |
| `page` | Physical PDF page, 1-based; worksheet/cell location or HTML section when applicable. |
| `extraction_method` | Actual extraction method: structured cells, PDF text/rules, reviewed manual transcription, prior verified embedded data, or an explicit sum. |
| `verification_status` | `source_table_reviewed` means a table context was inspected; `parsed_unreviewed` is an extraction without that review. This is separate from numerical checks. |
| `rule_validation` | `passed` means implemented numeric rules passed; it does not prove every value correct. `error` must be resolved before acceptance. |
| `ipeds_c1_check` | School-year C1 triple summary: `exact_match`, `difference_preserved`, or `not_available`. It applies to C1, not to all metrics in that row. |
| `notes` | Source versions, transformations, denominators, reporting changes, aid-year caveats and other limitations. |

Wide-table `source_urls` is a JSON array. `field_provenance` is a JSON object mapping every populated metric column to its source ID, page, extraction method and review status. Do not treat a row-level edition as provenance for every field when a row uses several section documents.

## Metrics

| Metrics | CDS concept | Unit / denominator |
|---|---|---|
| `applicants`, `admitted`, `enrolled` | C1 completed first-time, first-year applications, students offered admission, and enrolled students (FT + PT unless a population explicitly says otherwise) | Counts; same fall and reporting institution |
| `waitlist_offered` | C2 applicants offered a place on the waiting list | Count; not offers of admission |
| `waitlist_accepted` | C2 students accepting a waitlist place | Count; not matriculants |
| `waitlist_admitted` | C2 students subsequently admitted from the waitlist | Count; not necessarily enrolled |
| `sat_submit_pct`, `act_submit_pct` | C9 share of enrolled first-years submitting each test | Percent; groups may overlap; never sum to obtain test coverage |
| `sat_composite_p25/p50/p75` | C9 reported SAT composite percentiles | Scores, 400–1600; conditional on score submitters |
| `sat_ebrw_p25/p50/p75` | C9 SAT evidence-based reading/writing section percentiles | Scores, 200–800; conditional on submitters |
| `sat_math_p25/p50/p75` | C9 SAT math section percentiles | Scores, 200–800; conditional on submitters |
| `act_composite_p25/p50/p75` | C9 ACT composite percentiles | Scores, 1–36; conditional on submitters |
| `hs_rank_top10_pct`, `hs_rank_top25_pct`, `hs_rank_top50_pct` | C10 cumulative shares in the top tenth, quarter and half of the high-school class | Percent of students whose rank was reported, unless the source states a different denominator |
| `hs_rank_reported_pct` | C10 share of enrolled first-years reporting rank | Percent; needed to interpret rank statistics |
| `hs_gpa_mean` | C11/C12 reported mean high-school GPA for enrolled first-years | Source GPA scale; weighted, unweighted and UC GPA are not automatically comparable |
| `hs_gpa_*_pct` | C11/C12 reported GPA-band distribution, where collected | Percent; exact band is in the metric name and notes |
| `undergraduate_enrollment` | B1 degree-seeking and non-degree undergraduate census total as reported | Count; all undergraduates, not the C1 entering class |
| `aid_need_determined_count` | H2 students determined to have financial need | Count; specified full-time first-year or undergraduate population |
| `aid_need_based_received_count` | H2 students awarded need-based financial aid | Count; conditional population and aid reporting year retained |
| `aid_need_based_grant_received_count` | H2-E students awarded need-based scholarships or grants | Count; distinct from H2-D any financial aid |
| `aid_need_fully_met_count` | H2 students whose financial need was fully met, excluding PLUS, unsubsidized and private alternative loans as defined in the source | Count; source definition governs |
| `aid_need_met_pct` | H2 average percentage of demonstrated need met | Percent; not the percent of all students receiving aid |
| `aid_need_based_grant_mean_usd` | H2 average need-based scholarship/grant award among eligible recipients | USD; recipient mean, not average discount or net price for every student |

SAT composite percentiles are never created by adding section percentiles: quantiles of sums are not generally sums of quantiles. A missing median remains missing. Test-optional policies change the score-submitter population, so trends are descriptive rather than causal.

## Calculations and known boundaries

Admission rate can be calculated as `admitted / applicants`, and yield as `enrolled / admitted`, using matching C1 population, gender, residency, institution and year. Rates are not stored as independently sourced measurements. Do not combine systemwide counts with one campus, sum overlapping Emory school offers to infer unique people, or compare Purdue years without its reporting-footprint notes.

The panel is deliberately unbalanced. Coverage tables identify exactly which years and questions exist. A year in the title is the target scope, not a claim that every institution has all seven years or every requested question. C7 importance factors are optional and uncollected in this version unless an actual observation says otherwise. IPEDS 2024/2025 acquisition failures describe attempted endpoints, not proof those surveys do not exist.
