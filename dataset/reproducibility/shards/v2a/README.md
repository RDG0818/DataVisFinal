# CDS v2a extraction shard

## Coverage and provenance

This shard contains 149 observations for 17 Fall cohorts at 9 universities. Each school-year has the official CDS C1 applicants, admitted, and enrolled totals. The corresponding 17 source documents and their exact university URLs are in `sources.csv`. `observations.csv` carries the CDS section, 1-based physical PDF page or XLSX cell, cohort, population, unit, and extraction method for every value.

| University | Fall cohorts | Enhanced fields |
| --- | --- | --- |
| Northwestern | 2023, 2024 | C2 admitted from waitlist; C9 SAT/ACT submission |
| Dartmouth | 2023, 2024 | C2 waitlist; 2023 C10 class rank |
| Washington University in St Louis | 2023, 2024 | C2 where legible; C9; 2024 C10 rank and C12 GPA |
| Brandeis | 2023, 2024 | C2; C9; C10 rank; C12 GPA |
| Case Western Reserve | 2024 | C9; C10 rank; C12 GPA |
| Wake Forest | 2023, 2024 | C9; C10 rank |
| Lehigh | 2023, 2024 | C2; C9; C10 rank |
| William & Mary | 2023, 2024 | C2; 2023 C9 |
| Vanderbilt | 2023, 2024 | C2 admitted from waitlist; C9 |

The first 11 source documents were reviewed as university-hosted PDFs in the web PDF reader, with section headings and table context checked. Their hosts did not supply downloadable binaries locally, so `local_path` and `sha256` are blank and `status=official_web_render_reviewed` describes the narrower evidence. The subsequent six official binaries were recovered by a private Kaggle CPU job, linked into `raw/v2a/`, SHA256 checked against the recovery manifest, and reviewed via `pdftotext -layout` plus PDF form fields or sheet/cell text from XLSX. For those, source text is in `sources/v2a/`. The URLs and page or cell references let a reviewer reopen the exact tables.

## Transformation decisions

- C1 totals were taken from printed totals where available. When a CDS instead provided gender cells, the total is the sum of the reported cells and `extraction_method=derived_sum_of_reported_categories`. Dartmouth 2023 admitted is 919 + 878 = 1,797. Northwestern C1 sums all reported gender categories. No IPEDS value was used to fill a CDS cell.
- Missing, suppressed, and `do not publish` CDS cells are omitted. A printed numeric zero, such as Dartmouth's 2023 waitlist admitted, is retained.
- Rank percentiles describe entrants with reported rank, while `hs_rank_reported_pct` states the reported-rank share. Washington University 2024 GPA 4.19 is weighted and should not be pooled unqualified with unweighted GPA values.
- Case Western 2024 C9 prints ACT submission of 23%, while its ACT count of 269 is inconsistent with 1,619 enrolled. The source percentage is preserved with a note; no correction is inferred.
- Wake Forest 2024 and Lehigh 2024 are populated PDF forms. The web PDF text reader omitted form values, while the recovered official binaries expose them in local layout text and form fields. Wake Forest's optional residency totals are zero because unfilled; its C1 totals are sums of gender cells. Lehigh's C1 totals use its filled residency block.
- William & Mary 2023 workbook has zero-valued optional residency totals; its C1 values sum populated gender cells. William & Mary 2024 uses the coded CDS-C C117-C119 rows. Vanderbilt 2023 notes that its CDS/IPEDS applicant count is 935 lower than Vanderbilt's Factbook count due to a changed reporting rule; the CDS number is preserved. XLSX fraction cells for test-submission percentages were multiplied by 100.

## Attempted sources excluded from observations

- Brown's indexed older official PDF URL returned 404. Notre Dame's CDS PDFs redirect to a host returning 403. Georgetown and UPenn use Box links that could not be reviewed in this environment. NYU's official 2024 PDF returned 405. Tulane did not yield a readable official 2023/2024 CDS table in this pass. None were filled from third-party compilations.

## Shard validation

On 2026-10-26, a local CSV integrity check found 149 observation rows, 17 distinct official source URLs, 17 school-years with all three C1 totals, no duplicate metric keys, and no observation source URL absent from `sources.csv`. The six recovered binary SHA256 hashes match `raw/recovery/document_recovery.json`. This checks the shard structure and provenance; the earlier 11 web-rendered PDFs still lack binary hashes.
