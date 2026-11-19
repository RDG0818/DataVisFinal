# Private-university CDS shard

Run `python3 shards/private/extract_harvard.py` and then `python3 shards/private/compile_observations.py` from the workspace root. The latter is idempotent and writes `observations.csv` plus `sources.csv`.

The shard has 11 schools and 23 complete C1 school-years: Harvard (2019–24), Yale (2023–24), Princeton (2023–24), MIT (2023–24), Stanford (2023–24), Cornell (2023–24), Northwestern (2023–24), Columbia (2023–24), Brown and Dartmouth (2024), Duke (2023). Selected official C1 gender and residency cells are included. UPenn is absent because its official CDS is served by Box and could not be read directly here; numbers from independent compilations were **not** included.

Harvard PDFs are byte-hashed under `raw/private/`; extracted text is under `sources/private/`. Other sources were reviewed via official PDF search-index rendering, official MIT HTML, or the official Stanford Google Drive file through its connector. Exact official URLs and version caveats are in `sources.csv` and each observation. Blank fields are omitted. The OpenCDS transcriptions in `sources/private/opencds` were used only for source discovery, never as published numeric evidence.

For several indexed official PDFs, the C1 table was visible but physical PDF page could not be established because direct PDF fetch timed out. Their `page` value explicitly says `physical page unverified`; this is a release limitation. Stanford 2023 likewise has printed page only. Harvard, Yale 2024, Princeton 2024, Stanford 2024, Cornell 2023, and Duke 2023 have numeric physical C1 pages. MIT is official HTML.

Columbia's CDS covers Columbia College and Engineering, omitting the School of General Studies; its C1 totals cannot be equated with institution-wide IPEDS admissions. Cornell 2024 uses the official February 2025 v1 PDF; a later v6 PDF is linked at the university site but its C1 appears blank in web extraction. The original version is retained in the URL and note. Northwestern C2 offered/accepted values are suppressed, so only waitlist admits are included. Its 2024 B1 and C1 first-year gender categories differ by one student but both total 2,105; the C1 values are not changed.

H2 aid cohort year follows the academic year selected by H1: Harvard's 2024–25 edition reports *2023–24 final* aid and H2 observations use cohort_year 2023; Yale 2024–25 and Cornell 2023–24 use current-edition estimated aid. Aid recipient count is H2 D (any financial aid among those determined to have need); grant mean is H2 K. Princeton H2 was withheld because the indexed H1 checkbox layout did not establish the aid year confidently.

`source_table_reviewed` means the C1 row labels and numbers were inspected in the official source rendering; it does **not** imply a byte-hashed local PDF except Harvard. Physical page caveats remain explicit. IPEDS consistency is performed by the root integrator.
