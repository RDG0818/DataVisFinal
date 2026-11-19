"""Reviewed official Williams and Wellesley CDS tables; no IPEDS replacement."""
import csv,datetime,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OBS='school,unitid,cohort_year,cds_edition,section,metric,population,gender,residency,value,unit,source_url,page,extraction_method,verification_status,notes'.split(',')
SRC='school,unitid,cohort_year,cds_edition,source_url,local_path,sha256,retrieved_at,format,status,notes'.split(',')
docs=[
 dict(school='Williams College',unitid='168342',year=2023,url='https://www.williams.edu/institutional-research/files/2024/04/CDS_2023_2024_Williams_April2024.pdf',c1page=9,c2page=9,values=[11465,1145,541,1606,637,3],notes='Official C1 total column; gender collection mechanisms differ between applicants and enrolled students as the source notes.'),
 dict(school='Williams College',unitid='168342',year=2024,url='https://www.williams.edu/institutional-research/files/2025/06/CDS_2024_2025_Williams_V5.pdf',c1page=13,c2page=14,values=[15411,1272,547,2303,858,113],notes='Official C117-C119 total counts and C202-C204 waitlist counts. Unknown gender is separately reported; gender collection mechanisms differ.'),
 dict(school='Wellesley College',unitid='168218',year=2023,url='https://wellesley-college.files.svdcdn.com/production/administrative-departments/OIR/CDS_2023-2024-final-updated.pdf?dm=1723236940',c1page=15,c2page=15,values=[8184,1138,573,2389,1180,19],notes='Official C1 residency Total column p15 (same counts as reported women p14); official Wellesley CDS landing page links the university-controlled CDN.'),
 dict(school='Wellesley College',unitid='168218',year=2024,url='https://wellesley-college.files.svdcdn.com/production/administrative-departments/OIR/CDS_2024-2025-FINAL-1.pdf?dm=1762194243',c1page=11,c2page=11,values=[8714,1224,583,2495,1299,34],notes='Official C1 residency total and C2 totals. Official Wellesley public-data landing page links the university-controlled CDN.'),
]
records=[]
rp=ROOT/'raw/recovery/document_recovery.json'
recovered={r['url']:r for r in json.loads(rp.read_text()) if r.get('status')=='downloaded'} if rp.exists() else {}
sources=[]
for d in docs:
    year=d['year'];edition=f'{year}-{year+1}';rec=recovered.get(d['url'],{})
    local=ROOT/'raw/recovery'/rec.get('file','missing')
    exists=local.is_file()
    sources.append(dict(school=d['school'],unitid=d['unitid'],cohort_year=year,cds_edition=edition,source_url=d['url'],local_path=str(local.relative_to(ROOT)) if exists else '',sha256=hashlib.sha256(local.read_bytes()).hexdigest() if exists else '',retrieved_at=rec.get('retrieved_at','2026-10-26'),format='pdf',status='downloaded_and_official_table_reviewed' if exists else 'official_web_table_reviewed',notes=d['notes']))
    for i,(metric,value) in enumerate(zip(['applicants','admitted','enrolled','waitlist_offered','waitlist_accepted','waitlist_admitted'],d['values'])):
        records.append(dict(school=d['school'],unitid=d['unitid'],cohort_year=year,cds_edition=edition,section='C1' if i<3 else 'C2',metric=metric,population='first_time_first_year',gender='total',residency='all',value=value,unit='count',source_url=d['url'],page=d['c1page'] if i<3 else d['c2page'],extraction_method='manual_official_pdf_table_transcription',verification_status='source_table_reviewed',notes=d['notes']))
HERE.mkdir(exist_ok=True)
for name,rows,fields in [('observations.csv',records,OBS),('sources.csv',sources,SRC)]:
    with (HERE/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print(len(records),'observations from',len(sources),'official documents')
