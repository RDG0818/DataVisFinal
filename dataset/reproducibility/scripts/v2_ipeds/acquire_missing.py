"""Fetch only missing NCES ADM/HD complete data files in a private Kaggle CPU kernel."""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import zipfile
from pathlib import Path

import requests


OUT = Path('/kaggle/working')
OUT.mkdir(exist_ok=True)
needed = [(f'ADM{year}', year) for year in range(2014, 2019)]
needed += [(f'HD{year}', year) for year in range(2014, 2024)]
session = requests.Session()
records = []

for table, year in needed:
    url = f'https://nces.ed.gov/ipeds/datacenter/data/{table}.zip'
    rec = {'table': table, 'cohort_year': year, 'source_url': url,
           'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        resp = session.get(url, timeout=(12, 60))
        rec['http_status'] = resp.status_code
        rec['archive_bytes'] = len(resp.content)
        resp.raise_for_status()
        rec['archive_sha256'] = hashlib.sha256(resp.content).hexdigest()
        archive = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_members = [n for n in archive.namelist() if n.lower().endswith('.csv')]
        # Prefer revised files when the archive supplies both releases.
        exact = [n for n in csv_members if Path(n).stem.lower() in
                 {table.lower(), table.lower() + '_rv'}]
        if not exact:
            raise ValueError('No matching CSV member: ' + str(csv_members[:8]))
        member = sorted(exact, key=lambda n: (Path(n).stem.lower().endswith('_rv'), n))[-1]
        data = archive.read(member)
        if not data.lstrip().lower().startswith((b'unitid,', b'"unitid",', b'\xef\xbb\xbf')):
            raise ValueError('CSV header does not start with UNITID')
        name = table + '_official.csv'
        (OUT / name).write_bytes(data)
        rec.update(status='downloaded', archive_member=member,
                   local_file=name, csv_bytes=len(data),
                   csv_sha256=hashlib.sha256(data).hexdigest())
    except Exception as exc:
        rec.update(status='failed', error=repr(exc)[:500])
    records.append(rec)
    print(json.dumps(rec), flush=True)

(OUT / 'acquisition_manifest.json').write_text(json.dumps(records, indent=2) + '\n')
print('DOWNLOADED', sum(x['status'] == 'downloaded' for x in records), '/', len(needed), flush=True)
