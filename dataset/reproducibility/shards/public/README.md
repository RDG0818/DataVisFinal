# Public-university CDS shard

Run `python3 shards/public/build.py` from the workspace root to regenerate `observations.csv` and `sources.csv`. The script contains transcribed cells from official university Common Data Sets. `sources/public/` holds table-extraction evidence; `raw/public/` holds the official files that the local network allowed us to download. The source manifest records SHA-256 for downloaded files. Other PDFs were reviewed through the web PDF renderer at the stated official URL and physical page; their raw hashes remain blank.

The shard covers 11 schools; every school has a Fall 2022, 2023, or 2024 C1 triple for comparison to same-year IPEDS ADM. Rows use the CDS value as printed; IPEDS discrepancies must remain separate in `consistency.csv`. C1 totals derived from reported sex categories are explicitly marked `derived_sum_of_reported_categories`; direct residency totals take precedence when available. `page` is the 1-based physical PDF page or spreadsheet cell. `undergraduate_enrollment` includes all B1 undergraduates rather than only degree-seeking students. H2 rows represent full-time first-time first-year aid recipients; aid reporting year is specified in notes when it differs from the CDS entering cohort.

Special cases:

- Purdue is excluded: its 2024-25 and later CDS changes coverage from West Lafayette only to West Lafayette + Indianapolis + Polytechnic Statewide, and the official XLSX links were inaccessible locally. No combined-campus counts were assigned to West Lafayette.
- UCSB 2023 original CDS is hosted in a Google Drive file whose A0 respondent identifies UCSB Institutional Research and points to the school CDS page. The current school landing page links 2025 only; historical link provenance is weaker than for 2025 and is flagged in `sources.csv`.
- The UC schools often leave C9 blank due to test-blind admissions; blanks are omitted, not filled with zeros. UNC's published mean high school GPA exceeds 4.0 and is retained as reported, with a weighted-scale caution.
- UNC's 2023-24 CDS H2 section uses 2022-23 final aid data (H2 cohort_year corrected to 2022 by root review), whereas UCSB's 2025-26 and UCI's 2024-25 H2 sections use estimated data for the edition year. Treat aid figures as reported-year measures, not automatically the same C1 cohort.
- The PDF web renderer sometimes reorders visually adjacent values. Included counts were accepted only when table labels and total columns were inspected together. Some requested C7, C10, C11, C12, H2 and B1 fields remain sparse; this is a quality boundary, not a zero value.

Official Berkeley Google Sheet links are listed on https://opa.berkeley.edu/campus-data/common-data-set. The 2025 UCSB Drive PDF is linked by https://bap.ucsb.edu/index.php/institutional-research. Other official CDS landing pages are discoverable from the individual source URLs and notes.
