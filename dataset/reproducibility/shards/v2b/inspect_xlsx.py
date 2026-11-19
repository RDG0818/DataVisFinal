"""Small standard-library XLSX inspector for CDS workbooks."""
import sys, zipfile, xml.etree.ElementTree as ET
from pathlib import Path

N={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def read(path):
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            strings=[''.join(n.text or '' for n in si.findall('.//x:t',N)) for si in root.findall('x:si',N)]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets={x.attrib['Id']:x.attrib['Target'] for x in rel}
        for sheet in wb.findall('x:sheets/x:sheet',N):
            name=sheet.attrib['name'];target=targets[sheet.attrib['{'+N['r']+'}id']]
            part=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            root=ET.fromstring(z.read(part))
            rows=[]
            for row in root.findall('.//x:sheetData/x:row',N):
                cells=[]
                for c in row.findall('x:c',N):
                    v=c.find('x:v',N)
                    if v is not None:
                        value=strings[int(v.text)] if c.get('t')=='s' else v.text
                    else:
                        value=''.join(t.text or '' for t in c.findall('.//x:t',N))
                    if value:cells.append((c.get('r'),value))
                rows.append((int(row.get('r')),cells))
            yield name,rows

if __name__=='__main__':
    keywords=sys.argv[2:] or ['C1','C2','applied','admitted','enrolled']
    for name,rows in read(Path(sys.argv[1])):
        print('SHEET',name)
        hits=[i for i,(n,c) in enumerate(rows) if any(k.lower() in ' '.join(v for _,v in c).lower() for k in keywords)]
        wanted={j for i in hits for j in range(max(0,i-1),min(len(rows),i+2))}
        for j in sorted(wanted):
            n,c=rows[j]
            if c:print(n,' '.join(f'{ref}={v[:70]}' for ref,v in c)[:500])
