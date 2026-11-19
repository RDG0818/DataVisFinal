import requests,json,hashlib,datetime,subprocess,importlib.util
from pathlib import Path
OUT=Path('/kaggle/working'); records=[]
rows=[{'school': 'North Carolina State University at Raleigh', 'unitid': '199193', 'year': '2023', 'url': 'https://report.isa.ncsu.edu/ir/cds/pdfs/CDS_2023-24.v2.pdf', 'shard': 'v2b'}, {'school': 'North Carolina State University at Raleigh', 'unitid': '199193', 'year': '2024', 'url': 'https://report.isa.ncsu.edu/ir/cds/pdfs/CDS_2024-25.v3.pdf', 'shard': 'v2b'}, {'school': 'Clemson University', 'unitid': '217882', 'year': '2023', 'url': 'https://open.clemson.edu/cgi/viewcontent.cgi?article=1015&context=cds', 'shard': 'v2b'}, {'school': 'Clemson University', 'unitid': '217882', 'year': '2024', 'url': 'https://open.clemson.edu/cgi/viewcontent.cgi?article=1016&context=cds', 'shard': 'v2b'}]

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
                (OUT/(stem+'.txt')).write_text('\n'.join(blocks))
                rec['text_file']=stem+'.txt'
            except Exception as e:rec['text_error']=str(e)[:150]
    except Exception as e:rec.update(status='failed',error=str(e)[:250])
    records.append(rec)
    (OUT/'document_recovery.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(rec),flush=True)
print('DONE',sum(r['status']=='downloaded' for r in records),'/',len(records),flush=True)
