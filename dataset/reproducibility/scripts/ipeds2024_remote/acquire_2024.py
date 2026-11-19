"""Acquire newer official Access release when legacy survey URL returns 404."""
import csv, datetime, hashlib, io, json, shutil, subprocess, zipfile
from pathlib import Path
import requests

out=Path('/kaggle/working')
records=[]
url='https://nces.ed.gov/ipeds/tablefiles/zipfiles/IPEDS_2024-25_Provisional.zip'
rec={'source_url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    r=requests.get(url,timeout=90);rec.update(http_status=r.status_code,bytes=len(r.content));r.raise_for_status()
    rec['archive_sha256']=hashlib.sha256(r.content).hexdigest()
    z=zipfile.ZipFile(io.BytesIO(r.content));rec['members']=z.namelist()
    dbs=[n for n in z.namelist() if n.lower().endswith(('.mdb','.accdb'))]
    if not dbs:raise ValueError('No Access database member')
    db=out/'temporary_ipeds2024.accdb';db.write_bytes(z.read(dbs[0]))
    if not shutil.which('mdb-export'):
        subprocess.run(['sudo','apt-get','update','-qq'],check=True,timeout=120)
        subprocess.run(['sudo','apt-get','install','-y','-qq','mdbtools'],check=True,timeout=120)
    tables=subprocess.check_output(['mdb-tables','-1',str(db)],text=True).splitlines()
    rec['target_tables_found']=[t for t in tables if t.upper() in ['ADM2024','HD2024']]
    for name in rec['target_tables_found']:
        data=subprocess.check_output(['mdb-export',str(db),name],timeout=60)
        file=out/(name.upper()+'_official.csv');file.write_bytes(data)
        records.append({'table':name.upper(),'cohort_year':2024,'status':'downloaded',
            'official_source_url':url,'retrieval_url':url,'retrieved_at':rec['retrieved_at'],
            'acquisition':'direct_NCES_Access_database_via_private_Kaggle_CPU',
            'direct_NCES_acquisition_verified':True,'archive_member':dbs[0],
            'local_path':file.name,'sha256':hashlib.sha256(data).hexdigest()})
    db.unlink();rec['status']='processed'
except Exception as e:rec.update(status='failed',error=str(e)[:400])
records.append(rec)
for year,url in [(2023,'https://opair.psu.edu/files/2024/04/CDS_2023-2024_University_Park.pdf'),
                 (2024,'https://opair.psu.edu/files/2025/04/CDS_2024_2025_University_Park1.pdf')]:
    rec={'school':'Pennsylvania State University-Main Campus','cohort_year':year,'source_url':url}
    try:
        r=requests.get(url,timeout=15);rec.update(http_status=r.status_code,bytes=len(r.content));r.raise_for_status()
        if not r.content.startswith(b'%PDF'):raise ValueError('Not PDF')
        file=out/f'pennstate_{year}.pdf';file.write_bytes(r.content)
        rec.update(status='downloaded',local_path=file.name,sha256=hashlib.sha256(r.content).hexdigest())
    except Exception as e:rec.update(status='failed',error=str(e)[:300])
    records.append(rec)
(out/'official_newer_acquisition.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
