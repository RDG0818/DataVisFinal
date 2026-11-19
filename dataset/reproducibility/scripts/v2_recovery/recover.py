import requests,json,hashlib,datetime,subprocess,importlib.util
from pathlib import Path
OUT=Path('/kaggle/working'); records=[]
rows=[{'school': 'Purdue University-Main Campus', 'unitid': '243780', 'year': '2023', 'url': 'https://www.purdue.edu/idata/wp-content/uploads/2026/04/CDS_2023_2024.xlsx', 'shard': 'v2b'}, {'school': 'Purdue University-Main Campus', 'unitid': '243780', 'year': '2024', 'url': 'https://www.purdue.edu/idata/wp-content/uploads/2026/04/CDS_2024-2025.xlsx', 'shard': 'v2b'}, {'school': 'Pennsylvania State University-Main Campus', 'unitid': '214777', 'year': '2023', 'url': 'https://opair.psu.edu/files/2024/04/CDS_2023-2024_University_Park.pdf', 'shard': 'v2b'}, {'school': 'Pennsylvania State University-Main Campus', 'unitid': '214777', 'year': '2024', 'url': 'https://opair.psu.edu/files/2025/04/CDS_2024_2025_University_Park1.pdf', 'shard': 'v2b'}, {'school': 'Virginia Polytechnic Institute and State University', 'unitid': '233921', 'year': '2023', 'url': 'https://aie.vt.edu/content/dam/aie_vt_edu/common-data-set/23-24/CDS_2023-2024.pdf', 'shard': 'v2b'}, {'school': 'Wake Forest University', 'unitid': '199847', 'year': '2024', 'url': 'https://prod.wp.cdn.aws.wfu.edu/sites/202/2025/07/CDS-2024-2025-fillable-WFU.pdf', 'shard': 'v2a'}, {'school': 'Lehigh University', 'unitid': '213543', 'year': '2024', 'url': 'https://data.lehigh.edu/sites/data.lehigh.edu/files/6.20.2025_CDS-2024-2025_FINAL_REVISED.pdf', 'shard': 'v2a'}, {'school': 'William & Mary', 'unitid': '231624', 'year': '2024', 'url': 'https://www.wm.edu/offices/ir/university_data/cds/cds-2024-2025_c.pdf', 'shard': 'v2a'}, {'school': 'William & Mary', 'unitid': '231624', 'year': '2024', 'url': 'https://www.wm.edu/offices/ir/university_data/cds/wm_cds_2024-20252.xlsx', 'shard': 'v2a'}, {'school': 'William & Mary', 'unitid': '231624', 'year': '2023', 'url': 'https://www.wm.edu/offices/ir/university_data/cds/cds_2023_2024_working_may_2024.xlsx', 'shard': 'v2a'}, {'school': 'Vanderbilt University', 'unitid': '221999', 'year': '2024', 'url': 'https://cdn.vanderbilt.edu/vu-wpfsx/wp-content/uploads/sites/70/2025/11/CDS_2024-2025.xlsx', 'shard': 'v2a'}, {'school': 'Vanderbilt University', 'unitid': '221999', 'year': '2023', 'url': 'https://cdn.vanderbilt.edu/vu-wpfsx/wp-content/uploads/sites/70/2025/11/CDS_2023_2024_for_web_publishing.xlsx', 'shard': 'v2a'}, {'school': 'University of Notre Dame', 'unitid': '152080', 'year': '2024', 'url': 'https://www3.nd.edu/~instres/CDS/2024-2025/CDS_2024-2025.pdf', 'shard': 'v2a'}, {'school': 'University of Notre Dame', 'unitid': '152080', 'year': '2023', 'url': 'https://www3.nd.edu/~instres/CDS/2023-2024/CDS_2023-2024.pdf', 'shard': 'v2a'}, {'school': 'Brown University', 'unitid': '217156', 'year': '2024', 'url': 'https://oir.brown.edu/sites/default/files/2020-04/CDS_2024_2025.pdf', 'shard': 'v2a'}, {'school': 'New York University', 'unitid': '193900', 'year': '2024', 'url': 'https://www.nyu.edu/content/dam/nyu/institutionalResearch/documents/cds-on-website/2024-2025%20(pdf,%20file%20size%20907KB).pdf', 'shard': 'v2a'}, {'school': 'Bowdoin College', 'unitid': '161004', 'year': '2024', 'url': 'https://www.bowdoin.edu/ir/pdf/bowdoin_cds_2024-2025.pdf', 'shard': 'v2c'}, {'school': 'Williams College', 'unitid': '168342', 'year': '2024', 'url': 'https://www.williams.edu/institutional-research/files/2025/06/CDS_2024_2025_Williams_V5.pdf', 'shard': 'v2c'}, {'school': 'Williams College', 'unitid': '168342', 'year': '2023', 'url': 'https://www.williams.edu/institutional-research/files/2024/04/CDS_2023_2024_Williams_April2024.pdf', 'shard': 'v2c'}, {'school': 'Wellesley College', 'unitid': '168218', 'year': '2024', 'url': 'https://wellesley-college.files.svdcdn.com/production/administrative-departments/OIR/CDS_2024-2025-FINAL-1.pdf?dm=1762194243', 'shard': 'v2c'}, {'school': 'Wellesley College', 'unitid': '168218', 'year': '2023', 'url': 'https://wellesley-college.files.svdcdn.com/production/administrative-departments/OIR/CDS_2023-2024-final-updated.pdf?dm=1723236940', 'shard': 'v2c'}]

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
