import urllib.request, html.parser, urllib.parse, sys
class P(html.parser.HTMLParser):
 def __init__(self): super().__init__(); self.links=[]; self.href=None; self.txt=''
 def handle_starttag(self,tag,attrs):
  if tag=='a': self.href=dict(attrs).get('href'); self.txt=''
 def handle_data(self,data):
  if self.href is not None: self.txt+=data
 def handle_endtag(self,tag):
  if tag=='a' and self.href: self.links.append((self.txt.strip(),self.href)); self.href=None
for url in sys.argv[1:]:
 print('\nURL',url)
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  html=urllib.request.urlopen(req,timeout=20).read().decode('utf8','ignore'); p=P();p.feed(html)
  for title,href in p.links:
   if any(s in (title+' '+href).lower() for s in ['2025','2024','2023','2022','2021','2020','2019','cds','common data']): print(title[:65],urllib.parse.urljoin(url,href))
 except Exception as e: print('ERROR',e)
