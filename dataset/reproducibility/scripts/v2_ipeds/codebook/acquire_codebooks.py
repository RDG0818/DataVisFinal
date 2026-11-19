"""Acquire NCES official Access metadata workbooks for ADMCON7 code validation."""
import datetime as dt
import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path

import requests


OUT = Path('/kaggle/working')
records = []
for year in range(2015, 2023):
    collection = f'{year}{(year + 1) % 100:02d}'
    name = f'IPEDS{collection}Tablesdoc.xlsx'
    url = f'https://nces.ed.gov/ipeds/tablefiles/tableDocs/{name}'
    rec = {'cohort_year': year, 'url': url,
           'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=(12, 60))
        rec['http_status'] = response.status_code
        response.raise_for_status()
        data = response.content
        if not zipfile.is_zipfile(BytesIO(data)):
            raise ValueError('Response is not an xlsx ZIP file')
        (OUT / name).write_bytes(data)
        rec.update(status='downloaded', local_file=name, bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest())
    except Exception as exc:
        rec.update(status='failed', error=repr(exc)[:500])
    records.append(rec)
    print(json.dumps(rec), flush=True)

(OUT / 'codebook_acquisition.json').write_text(json.dumps(records, indent=2) + '\n')
