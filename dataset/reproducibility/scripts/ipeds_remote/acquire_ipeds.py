"""Bounded official NCES acquisition. Private CPU utility; no model fitting."""
import requests, zipfile, io, hashlib, json, datetime
from pathlib import Path

out=Path('/kaggle/working')
records=[]
s=requests.Session()
for year in range(2019,2026):
    table=f'ADM{year}'
    urls=[f'https://nces.ed.gov/ipeds/datacenter/data/{table}.zip',
          f'https://nces.ed.gov/ipeds/data-generator?year={year}&tableName={table}&HasRV=0&type=csv']
    for url in urls:
        rec={'table':table,'cohort_year':year,'official_source_url':url,
             'retrieval_url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'acquisition':'direct_NCES_via_private_Kaggle_CPU','direct_NCES_acquisition_verified':False}
        try:
            r=s.get(url,timeout=12)
            rec.update(http_status=r.status_code,bytes=len(r.content))
            r.raise_for_status()
            if r.content[:2]==b'PK':
                z=zipfile.ZipFile(io.BytesIO(r.content))
                files=[n for n in z.namelist() if n.lower().endswith('.csv')]
                if not files: raise ValueError('No CSV in ZIP')
                # Prefer published revised table if present; keep exact member name.
                member=sorted(files,key=lambda n:('_rv' in n.lower(),n))[-1]
                data=z.read(member);rec['archive_member']=member
            elif r.content.lstrip().startswith((b'"UNITID"',b'UNITID',b'\xef\xbb\xbf')):
                data=r.content
            else:raise ValueError('Response is not CSV/ZIP')
            name=table+'_official.csv';(out/name).write_bytes(data)
            rec.update(status='downloaded',sha256=hashlib.sha256(data).hexdigest(),
                local_path=name,direct_NCES_acquisition_verified=True)
            records.append(rec);print(json.dumps(rec),flush=True);break
        except Exception as e:
            rec.update(status='failed',error=str(e)[:300]);records.append(rec)
            print(json.dumps(rec),flush=True)
(out/'ipeds_acquisition.json').write_text(json.dumps(records,indent=2))
print('SUCCESSFUL_TABLES',sum(r['status']=='downloaded' for r in records),flush=True)
