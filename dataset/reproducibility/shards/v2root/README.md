# Root supplement: Williams and Wellesley

Two well-known liberal arts colleges, both Fall 2023 and Fall 2024. C1 and C2 were read in the official PDF table context, with 1-based physical page locations. Williams uses reported total columns; Wellesley uses its explicitly reported residency Total column. Neither CDS is filled from IPEDS. Wellesley source URLs are the university-controlled CDN linked from https://www.wellesley.edu/about-us/offices-departments/office-of-institutional-research/public-data . Williams source landing page: https://hub.williams.edu/institutional-research/common-data-set/ .

Web PDF screenshots returned references without visible pixels. No visual screenshot inspection is claimed on that basis; the labeled table text was reviewed. A private Kaggle document recovery task is also obtaining original bytes and text; build.py includes a SHA-256 only when the actual downloaded original exists locally. Numeric observations are intentionally limited to the unambiguous C1/C2 fields.

Original Wellesley 2023 p15 and 2024 p11 were recovered and visually inspected after Poppler rendering; the six C1/C2 values in each year match the rendered tables. Evidence images are in sources/v2root/. Williams remains a reviewed official web-PDF table without a binary hash (remote original returned 403).
