import requests,pathlib
names={'Harvard':'Harvard','Yale':'Yale','Princeton':'Princeton','MIT':'MIT','Stanford':'Stanford','Columbia':'Columbia','UPenn':'UPenn','Cornell':'Cornell','Brown':'Brown','Dartmouth':'Darmouth','Duke':'Duke','Northwestern':'Northwestern'}
p=pathlib.Path('sources/private/opencds');p.mkdir(parents=True,exist_ok=True)
for school,name in names.items():
 u=f'https://raw.githubusercontent.com/htansetiawan/OpenCDS/main/documents/{name}-2024-2025.md'
 try:
  r=requests.get(u,timeout=15);r.raise_for_status();(p/f'{school}.md').write_bytes(r.content);print(school,len(r.content),flush=True)
 except Exception as e:print(school,repr(e),flush=True)
