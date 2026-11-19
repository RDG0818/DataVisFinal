# CDS v2c extraction

`python3 shards/v2c/build.py` regenerates `observations.csv` and `sources.csv` from official CDS pages. The shard contains 6 institutions, each with Fall 2023 and Fall 2024 C1 applicants/admitted/enrolled; 12 school-years and 236 reported observations. All school-years include C2 and C9 values where the institution reported them. Total counts were taken from a published total column, not IPEDS.

## Evidence and limits

- Ten school-years have local official PDFs under `raw/v2c/`, SHA-256 hashes in `sources.csv`, and physical C1/C2 pages inspected as rendered images. Bowdoin 2024 and Carleton 2023 came from the first acquisition; eight additional PDFs from the second private Kaggle acquisition. C9 tables were checked in local PDF text with headings and 1-based physical page references.
- Amherst 2023 and 2024 have official PDF URLs and were read through the web PDF index, which exposed full C1/C2/C9 table text and physical page markers. Direct binary download returned HTTP 405, so `local_path` and `sha256` are blank. Their `sources.csv` status and `extraction_method` explicitly flag the different evidence route; no image review is claimed.
- Bowdoin's C2 offered and accepted fields are blank or N/A; only the published waitlist admitted counts are included. Missing fields were not assigned zero.
- Middlebury labels Fall 2024 C1 admitted/enrolled and some C2 metrics "September Only"; Fall 2023 C2 accepted/admitted are also labeled "Fall Only." The values are preserved with row notes and should not be silently equated to a full September-plus-February intake.
- Swarthmore official PDF requests returned an anti-bot HTML page in the private acquisition; Pomona's current official CDS links resolve through Tableau or Box. Neither school was added without a reviewable official C1 table.

The contract is in `SHARD_CONTRACT.md`. This shard does not alter IPEDS data and does not reconcile CDS/IPEDS disagreements.
