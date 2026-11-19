"""Create one private, bounded official-document recovery kernel."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
batch=3 if '--batch-three' in sys.argv else 2 if '--incremental' in sys.argv else 1
incremental=batch>1
D=ROOT/('scripts/v2_recovery'+str(batch) if incremental else 'scripts/v2_recovery');D.mkdir(exist_ok=True)
rows=[]
for p in ROOT.glob('shards/v2*/recovery_sources.csv'):
    rows.extend(dict(r,shard=p.parent.name) for r in csv.DictReader(p.open()))
rows.extend([
 {'school':'Bowdoin College','unitid':'161004','year':'2024','url':'https://www.bowdoin.edu/ir/pdf/bowdoin_cds_2024-2025.pdf','shard':'v2c'},
 {'school':'Williams College','unitid':'168342','year':'2024','url':'https://www.williams.edu/institutional-research/files/2025/06/CDS_2024_2025_Williams_V5.pdf','shard':'v2c'},
 {'school':'Williams College','unitid':'168342','year':'2023','url':'https://www.williams.edu/institutional-research/files/2024/04/CDS_2023_2024_Williams_April2024.pdf','shard':'v2c'},
 {'school':'Wellesley College','unitid':'168218','year':'2024','url':'https://wellesley-college.files.svdcdn.com/production/administrative-departments/OIR/CDS_2024-2025-FINAL-1.pdf?dm=1762194243','shard':'v2c'},
 {'school':'Wellesley College','unitid':'168218','year':'2023','url':'https://wellesley-college.files.svdcdn.com/production/administrative-departments/OIR/CDS_2023-2024-final-updated.pdf?dm=1723236940','shard':'v2c'}])
if incremental:
    attempted={r['url'] for p in (ROOT/'raw').glob('recovery*/document_recovery.json') for r in json.loads(p.read_text())}
    rows=[r for r in rows if r['url'] not in attempted]
code='''import requests,json,hashlib,datetime,subprocess,importlib.util
from pathlib import Path
OUT=Path('/kaggle/working'); records=[]
'''+f'rows={rows!r}\n'+'''
for i,r in enumerate(rows):
    rec=dict(r,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        resp=requests.get(r['url'],timeout=22);rec['http_status']=resp.status_code
        resp.raise_for_status();data=resp.content
        if data.startswith(b'%PDF'):ext='.pdf'
        elif data.startswith(b'PK'):ext='.xlsx'
        else:raise ValueError('Not a PDF or XLSX archive')
        stem=f"{r['shard']}_{r['unitid']}_{r['year']}_{i:02d}"
        dest=OUT/(stem+ext);dest.write_bytes(data)
        rec.update(status='downloaded',file=dest.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        if ext=='.pdf':
            try:
                subprocess.run(['pdftotext','-layout',str(dest),str(OUT/(stem+'.txt'))],check=True,timeout=25,capture_output=True)
                rec['text_file']=stem+'.txt'
            except Exception as e:rec['text_error']=str(e)[:150]
            try:
                from pypdf import PdfReader
                reader=PdfReader(dest)
                fields=reader.get_fields() or {}
                (OUT/(stem+'_fields.json')).write_text(json.dumps({k:{str(kk):str(vv) for kk,vv in v.items()} for k,v in fields.items()},indent=2))
                rec['form_fields']=len(fields)
            except Exception as e:rec['form_error']=str(e)[:150]
        else:
            try:
                import openpyxl
                wb=openpyxl.load_workbook(dest,data_only=True,read_only=True)
                blocks=[]
                for ws in wb:
                    blocks.append('SHEET '+ws.title)
                    for row in ws:
                        vals=[f'{cell.coordinate}={cell.value}' for cell in row if cell.value is not None]
                        if vals:blocks.append(' | '.join(vals))
                (OUT/(stem+'.txt')).write_text('\\n'.join(blocks))
                rec['text_file']=stem+'.txt'
            except Exception as e:rec['text_error']=str(e)[:150]
    except Exception as e:rec.update(status='failed',error=str(e)[:250])
    records.append(rec)
    (OUT/'document_recovery.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(rec),flush=True)
print('DONE',sum(r['status']=='downloaded' for r in records),'/',len(records),flush=True)
'''
(D/'recover.py').write_text(code)
suffix=' batch three' if batch==3 else ' batch two' if batch==2 else ''
m={'id':'yangkuangou/cds-v2-private-document-recovery'+suffix.replace(' ','-'),'title':'CDS v2 private document recovery'+suffix,'code_file':'recover.py','language':'python','kernel_type':'script','is_private':True,'enable_gpu':False,'enable_internet':True,'dataset_sources':[],'competition_sources':[],'kernel_sources':[]}
(D/'kernel-metadata.json').write_text(json.dumps(m,indent=2))
print('Created bounded recovery for',len(rows),'known official URLs')
