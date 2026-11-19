import zipfile,xml.etree.ElementTree as ET,sys,re
p=sys.argv[1];z=zipfile.ZipFile(p)
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
shared=[]
if 'xl/sharedStrings.xml' in z.namelist():
 root=ET.fromstring(z.read('xl/sharedStrings.xml'))
 for si in root.findall('m:si',ns): shared.append(''.join((t.text or '') for t in si.findall('.//m:t',ns)))
wb=ET.fromstring(z.read('xl/workbook.xml'))
rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
rd={x.get('Id'):x.get('Target') for x in rels}
for sheet in wb.findall('m:sheets/m:sheet',ns):
 name=sheet.get('name');rid=sheet.get('{'+ns['r']+'}id');target=rd[rid].lstrip('/')
 path=target if target.startswith('xl/') else 'xl/'+target
 if not path in z.namelist():continue
 root=ET.fromstring(z.read(path))
 print('\nSHEET',name,path)
 for row in root.findall('.//m:sheetData/m:row',ns):
  values=[]
  for cell in row.findall('m:c',ns):
   typ=cell.get('t');v=cell.find('m:v',ns);inline=cell.find('m:is',ns)
   if v is not None: val=shared[int(v.text)] if typ=='s' else v.text
   elif inline is not None: val=''.join((t.text or '') for t in inline.findall('.//m:t',ns))
   else:continue
   if val not in ('',None):values.append((cell.get('r'),val))
  if any(re.search(r'first.time|applicant|enroll|admit|C1\b|wait',str(v),re.I) for c,v in values):
   print('ROW',row.get('r'),values[:15])
