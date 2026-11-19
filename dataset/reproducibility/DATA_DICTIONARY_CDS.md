# Data dictionary — US College Admissions CDS Panel

A source-preserving, unbalanced institution × entering-fall-cohort panel. The data are institutional descriptions, not estimates of an individual applicant's chance of admission. Blank means unavailable, uncollected, not applicable, or not yet verified; it never means zero.

## Files and keys

- `cds_long.csv`: one numeric observation per `(unitid, cohort_year, section, metric, population, gender, residency)`. It is the authoritative table for field-level provenance.
- `cds_wide.csv`: one row per `(unitid, cohort_year)`. Columns suffix a non-default population, gender, or residency with `__population_…`, `__gender_…`, or `__residency_…`. Empty expected metric columns are intentional.
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
