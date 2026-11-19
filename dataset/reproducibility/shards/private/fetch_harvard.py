import requests,hashlib,csv,datetime,subprocess,pathlib
P=pathlib.Path('raw/private'); P.mkdir(parents=True,exist_ok=True)
T=pathlib.Path('sources/private'); T.mkdir(parents=True,exist_ok=True)
base='https://bpb-us-e1.wpmucdn.com/sites.harvard.edu/dist/6/210/files/'
urls={
2019:base+'2023/02/harvard_cds_2019-2020.pdf',
2020:base+'2023/02/harvard_cds_2020-2021.pdf',
2021:base+'2023/06/harvard_cds_2021-2022_revised.pdf',
2022:base+'2023/06/harvard_cds_2022-2023.pdf',
2023:base+'2024/05/CDS_2023-2024-Final-4755619e875b1241.pdf',
2024:base+'2025/06/HarvardUniversity_CDS_2024-2025.pdf',
}
fields='school unitid cohort_year cds_edition source_url local_path sha256 retrieved_at format status notes'.split()
rows=[]
for y,u in urls.items():
 try:
  r=requests.get(u,timeout=25);r.raise_for_status()
  if not r.content.startswith(b'%PDF'):raise ValueError('not PDF')
  p=P/f'harvard_{y}.pdf';p.write_bytes(r.content)
  subprocess.run(['pdftotext','-layout',str(p),str(T/f'harvard_{y}.txt')],check=True)
  status='downloaded'; sha=hashlib.sha256(r.content).hexdigest();notes=''
  print(y,len(r.content),sha[:12])
 except Exception as e:
  p='';sha='';status='error';notes=repr(e);print(y,notes)
 rows.append(dict(school='Harvard University',unitid=166027,cohort_year=y,cds_edition=f'{y}-{y+1}',source_url=u,local_path=str(p),sha256=sha,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),format='pdf',status=status,notes=notes))
with open('shards/private/sources.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
