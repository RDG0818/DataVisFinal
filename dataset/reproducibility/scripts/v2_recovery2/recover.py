import requests,json,hashlib,datetime,subprocess,importlib.util
from pathlib import Path
OUT=Path('/kaggle/working'); records=[]
rows=[{'school': 'Swarthmore College', 'unitid': '216287', 'year': '2024', 'url': 'https://www.swarthmore.edu/sites/default/files/assets/documents/institutional-effectiveness-research-assessment/Swarthmore-College-CDS-2024-2025-excel-version.pdf', 'shard': 'v2c'}, {'school': 'Swarthmore College', 'unitid': '216287', 'year': '2023', 'url': 'https://www.swarthmore.edu/sites/default/files/assets/documents/institutional-effectiveness-research-assessment/Swarthmore%20CDS%202023-2024.pdf', 'shard': 'v2c'}, {'school': 'Amherst College', 'unitid': '164465', 'year': '2024', 'url': 'https://www.amherst.edu/system/files/C%20First-Time,%20First-Year%20Admission_4.pdf', 'shard': 'v2c'}, {'school': 'Amherst College', 'unitid': '164465', 'year': '2023', 'url': 'https://www.amherst.edu/system/files/2023%20C%20FTFT%20Admission%20Revised%20FINAL.pdf', 'shard': 'v2c'}, {'school': 'Claremont McKenna College', 'unitid': '112260', 'year': '2024', 'url': 'https://www.cmc.edu/sites/default/files/CDS_2024-2025.pdf', 'shard': 'v2c'}, {'school': 'Claremont McKenna College', 'unitid': '112260', 'year': '2023', 'url': 'https://www.cmc.edu/sites/default/files/CDS_2023_2024%20V2.pdf', 'shard': 'v2c'}, {'school': 'Harvey Mudd College', 'unitid': '115409', 'year': '2024', 'url': 'https://www.hmc.edu/institutional-research/wp-content/uploads/sites/42/2024/12/CDS-2024-2025-SharedtoWeb.pdf', 'shard': 'v2c'}, {'school': 'Harvey Mudd College', 'unitid': '115409', 'year': '2023', 'url': 'https://www.hmc.edu/institutional-research/wp-content/uploads/sites/42/2024/10/CDS_2023-2024_Complete_V3.pdf', 'shard': 'v2c'}, {'school': 'Bowdoin College', 'unitid': '161004', 'year': '2023', 'url': 'https://www.bowdoin.edu/ir/pdf/bowdoin-cds_2023-2024.pdf', 'shard': 'v2c'}, {'school': 'Carleton College', 'unitid': '173258', 'year': '2024', 'url': 'https://carleton-wp-production.s3.amazonaws.com/uploads/sites/292/2025/07/2024-2025-CDS_06032025.pdf', 'shard': 'v2c'}, {'school': 'Middlebury College', 'unitid': '230959', 'year': '2024', 'url': 'https://www.middlebury.edu/sites/default/files/2025-04/Middlebury%20CDS%202024_2025.pdf?fv=_3Gr6e2c', 'shard': 'v2c'}, {'school': 'Middlebury College', 'unitid': '230959', 'year': '2023', 'url': 'https://www.middlebury.edu/sites/default/files/2024-05/CDS_2023_2024%20completed%205.15.24_0.pdf?fv=1KqsLYZg', 'shard': 'v2c'}, {'school': 'Ohio State University-Main Campus', 'unitid': '204796', 'year': '2024', 'url': 'https://irp.osu.edu/media/276', 'shard': 'v2b'}, {'school': 'University of Maryland-College Park', 'unitid': '163286', 'year': '2023', 'url': 'https://www.irpa.umd.edu/InstitutionalData/CommonDataSet/CDS_2023-2024.xlsx', 'shard': 'v2b'}, {'school': 'University of Maryland-College Park', 'unitid': '163286', 'year': '2024', 'url': 'https://www.irpa.umd.edu/InstitutionalData/CommonDataSet/CDS_2024-2025.xlsx', 'shard': 'v2b'}, {'school': 'University of Washington-Seattle Campus', 'unitid': '236948', 'year': '2023', 'url': 'https://finance.uw.edu/iads/files/docs/ipeds/common_data_set/cds_seattle_2023_2024.xlsx', 'shard': 'v2b'}, {'school': 'University of Washington-Seattle Campus', 'unitid': '236948', 'year': '2024', 'url': 'https://finance.uw.edu/iads/files/docs/ipeds/common_data_set/cds_2024-2025_seattle.pdf', 'shard': 'v2b'}]

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
