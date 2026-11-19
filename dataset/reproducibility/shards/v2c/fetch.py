"""Bounded single-thread downloads of school-hosted CDS source PDFs."""
import csv
import datetime as dt
import hashlib
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'raw/v2c'
RAW.mkdir(parents=True, exist_ok=True)
SOURCES = [
    ('Swarthmore College', 216287, 2024, 'https://www.swarthmore.edu/sites/default/files/assets/documents/institutional-effectiveness-research-assessment/Swarthmore-College-CDS-2024-2025-excel-version.pdf'),
    ('Swarthmore College', 216287, 2023, 'https://www.swarthmore.edu/sites/default/files/assets/documents/institutional-effectiveness-research-assessment/Swarthmore%20CDS%202023-2024.pdf'),
    ('Amherst College', 164465, 2024, 'https://www.amherst.edu/system/files/C%20First-Time,%20First-Year%20Admission_4.pdf'),
    ('Amherst College', 164465, 2023, 'https://www.amherst.edu/system/files/2023%20C%20FTFT%20Admission%20Revised%20FINAL.pdf'),
    ('Claremont McKenna College', 112260, 2024, 'https://www.cmc.edu/sites/default/files/CDS_2024-2025.pdf'),
    ('Claremont McKenna College', 112260, 2023, 'https://www.cmc.edu/sites/default/files/CDS_2023_2024%20V2.pdf'),
    ('Harvey Mudd College', 115409, 2024, 'https://www.hmc.edu/institutional-research/wp-content/uploads/sites/42/2024/12/CDS-2024-2025-SharedtoWeb.pdf'),
    ('Harvey Mudd College', 115409, 2023, 'https://www.hmc.edu/institutional-research/wp-content/uploads/sites/42/2024/10/CDS_2023-2024_Complete_V3.pdf'),
    ('Bowdoin College', 161004, 2024, 'https://www.bowdoin.edu/ir/pdf/bowdoin_cds_2024-2025.pdf'),
    ('Bowdoin College', 161004, 2023, 'https://www.bowdoin.edu/ir/pdf/bowdoin-cds_2023-2024.pdf'),
    ('Carleton College', 173258, 2024, 'https://carleton-wp-production.s3.amazonaws.com/uploads/sites/292/2025/07/2024-2025-CDS_06032025.pdf'),
    ('Carleton College', 173258, 2023, 'https://carleton-wp-production.s3.amazonaws.com/uploads/sites/292/2024/05/CDS_UNL2_2023_2024_Carleton-FINAL.pdf'),
    ('Middlebury College', 230959, 2024, 'https://www.middlebury.edu/sites/default/files/2025-04/Middlebury%20CDS%202024_2025.pdf?fv=_3Gr6e2c'),
    ('Middlebury College', 230959, 2023, 'https://www.middlebury.edu/sites/default/files/2024-05/CDS_2023_2024%20completed%205.15.24_0.pdf?fv=1KqsLYZg'),
]

def main():
    rows=[]
    session=requests.Session()
    session.headers['User-Agent']='Mozilla/5.0 (compatible; CDS research extraction)'
    for school,uid,year,url in SOURCES:
        name=f'{uid}_{year}.pdf';target=RAW/name
        rec=dict(school=school,unitid=uid,cohort_year=year,cds_edition=f'{year}-{year+1}',
                 source_url=url,local_path='',sha256='',retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                 format='pdf',status='',notes='')
        try:
            response=session.get(url,timeout=(8,25),allow_redirects=True)
            response.raise_for_status()
            data=response.content
            if len(data)>18_000_000 or not data.startswith(b'%PDF'):
                raise ValueError(f'Unexpected response size/signature: {len(data)} bytes')
            target.write_bytes(data)
            rec.update(local_path=str(target.relative_to(ROOT)),sha256=hashlib.sha256(data).hexdigest(),
                       status='downloaded',notes=f'HTTP {response.status_code}; {len(data)} bytes; final URL {response.url}')
        except Exception as exc:
            rec.update(status='failed',notes=repr(exc)[:400])
        rows.append(rec)
        print(school,year,rec['status'],rec['notes'][:130],flush=True)
    with (ROOT/'shards/v2c/source_candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)

if __name__=='__main__':main()
