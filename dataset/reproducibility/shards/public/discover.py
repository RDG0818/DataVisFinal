from html.parser import HTMLParser
from urllib.parse import urljoin
import requests,re
class Links(HTMLParser):
 def __init__(self): super().__init__();self.href='';self.text='';self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a': self.href=dict(attrs).get('href','');self.text=''
 def handle_data(self,data):
  if self.href:self.text+=data
 def handle_endtag(self,tag):
  if tag=='a' and self.href: self.links.append((self.text.strip(),self.href));self.href='';self.text=''
urls={
'UCLA':'https://apb.ucla.edu/campus-statistics/common-data-set-undergraduate-profile',
'Berkeley':'https://opa.berkeley.edu/campus-data/common-data-set',
'UCSD':'https://ir.ucsd.edu/stats/undergrad/common-data-set.html',
'UCI':'https://irap.uci.edu/institutional-research/data-hub/common-data-set/',
'UCD':'https://aggiedata.ucdavis.edu/common-data-set',
'UCSC':'https://iraps.ucsc.edu/about-ucsc/common-data-set/',
'UCR':'https://ir.ucr.edu/cds',
'UCSB':'https://bap.ucsb.edu/index.php/institutional-research',
'Michigan':'https://obp.umich.edu/campus-statistics/common-data-set/',
'Purdue':'https://www.purdue.edu/idata/products-services/common-data-set/',
'Virginia':'https://ira.virginia.edu/common-data-set',
}
for k,u in urls.items():
 try:
  r=requests.get(u,timeout=15);p=Links();p.feed(r.text)
  print('\n',k,r.status_code,r.url,flush=True)
  for t,h in p.links:
   if re.search(r'2019|2020|2021|2022|2023|2024|2025|CDS',t+' '+h,re.I):
    print(t[:45],urljoin(r.url,h)[:170],flush=True)
 except Exception as e: print(k,'ERROR',type(e).__name__,str(e)[:100],flush=True)
