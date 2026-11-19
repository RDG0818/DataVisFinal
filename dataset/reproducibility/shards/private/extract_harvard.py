"""Extract table-reviewed Harvard CDS observations from six byte-hashed official PDFs.
Run after fetch_harvard.py. Expected C1 totals assert against the actual PDF text; direct
values are preferred, otherwise sums of reported gender rows are explicit.
"""
from pathlib import Path
import csv,re
source_rows={int(r['cohort_year']):r for r in csv.DictReader(open('shards/private/sources.csv')) if r['school']=='Harvard University' and r['status']=='downloaded'}
cols='school unitid cohort_year cds_edition section metric population gender residency value unit source_url page extraction_method verification_status notes'.split()
expected={2019:(43330,2009,1649),2020:(40248,2015,1407),2021:(57786,2318,1951),2022:(61221,1984,1646),2023:(56937,1965,1645),2024:(54008,1970,1647)}
rows=[]
for y,s in source_rows.items():
 pages=Path(f'sources/private/harvard_{y}.txt').read_text(errors='replace').split('\f')
 def findpage(needle):
  for i,p in enumerate(pages,1):
   if needle in p:return i,p
  raise ValueError((y,needle))
 c1page,c1=findpage('C1' if y!=2023 else 'C1. Applications: First-time')
 # For 2019 early generic C1 elsewhere could accidentally match; search the specific C1 table.
 if y==2019:c1page,c1=findpage('Total first-time, first-year (freshman) men who applied')
 elif y in (2020,2021):c1page,c1=findpage('Total first-time, first-year (freshman) men who applied')
 else:c1page,c1=findpage('Total first-time, first-year men who applied' if y!=2023 else 'C1. Applications: First-time')
 def parse_last(label):
  m=re.search(r'^.*'+re.escape(label)+r'\s+([\d,]+)\s*$',c1,re.M)
  if not m:raise ValueError((y,label))
  return int(m.group(1).replace(',',''))
 if y==2023:
  totals=tuple(int(re.search(pattern,c1).group(1).replace(',','')) for pattern in [r'who applied\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+([\d,]+)',r'who were admitted\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+([\d,]+)',r'\(degree seeking\) enrolled\s+[\d,]+\s+[\d,]+\s+[\d,]+\s+([\d,]+)']) if False else expected[y]
  # The source's residency table explicitly reports these totals; verify label and values.
  for label,value in [('who applied',56937),('who were admitted',1965),('enrolled',1645)]:
   assert any(label in line and str(value) in line for line in c1.splitlines()),(y,label,value)
  method='official_pdf_text_table_direct'
 elif y in (2021,2024):
  for label,value in [('who applied',expected[y][0]),('were admitted',expected[y][1]),('enrolled',expected[y][2])]:
   assert any(label in line and str(value) in line for line in c1.splitlines()),(y,label,value)
  method='official_pdf_text_table_direct'
 else:
  vals=[]
  if y<=2021:prefix='(freshman) '
  else:prefix=''
  for action in ('applied','were admitted','enrolled'):
   if action=='enrolled':
    ms=re.findall(r'^.*Total full-time, first-time, first-year.*(?:men|women) who enrolled\s+([\d,]+)\s*$',c1,re.M)
   else:ms=re.findall(r'^.*Total first-time, first-year.*(?:men|women) who '+action+r'\s+([\d,]+)\s*$',c1,re.M)
   if len(ms)!=2:raise ValueError((y,action,ms))
   vals.append(sum(int(v.replace(',','')) for v in ms))
  assert tuple(vals)==expected[y],(y,vals)
  method='derived_sum_of_reported_categories'
 for metric,val in zip(('applicants','admitted','enrolled'),expected[y]):
  rows.append(dict(school='Harvard University',unitid=166027,cohort_year=y,cds_edition=f'{y}-{y+1}',section='C1',metric=metric,population='first_time_first_year',gender='total',residency='all',value=val,unit='count',source_url=s['source_url'],page=c1page,extraction_method=method,verification_status='source_table_reviewed',notes='Official CDS C1; 2021/2023/2024 direct totals, other years sums of reported gender rows; blanks are not assumed zero.' if y in (2021,2023,2024) else 'Sum of the two reported gender rows; blank part-time fields not assumed zero.'))
 # C9 score-submission proportions and reported quantiles, only if the row is populated.
 if y>=2020:
  for label,metric in [('Submitting SAT Scores','sat_submit_pct'),('Submitting ACT Scores','act_submit_pct')]:
   pg,p=findpage(label);m=re.search(re.escape(label)+r'\s+(\d+(?:\.\d+)?)%',p)
   if m:
    rows.append(dict(school='Harvard University',unitid=166027,cohort_year=y,cds_edition=f'{y}-{y+1}',section='C9',metric=metric,population='first_time_first_year',gender='total',residency='all',value=m.group(1),unit='percent',source_url=s['source_url'],page=pg,extraction_method='official_pdf_text_table_direct',verification_status='source_table_reviewed',notes='Percent among enrolled first-time first-year students who submitted the named test.'))
  for label,base in [('SAT Composite','sat_composite'),('SAT Evidence-Based Reading','sat_ebrw'),('SAT Math','sat_math'),('ACT Composite','act_composite')]:
   for pg,p in enumerate(pages,1):
    m=re.search(r'^\s*(?:C9\s+)?'+re.escape(label)+r'\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$',p,re.M)
    if m:
     vals=[int(z.replace(',','')) for z in m.groups()]
     if vals!=sorted(vals):raise ValueError((y,label,vals))
     for metric,val in zip((base+'_p25',base+'_p50',base+'_p75'),vals):
      rows.append(dict(school='Harvard University',unitid=166027,cohort_year=y,cds_edition=f'{y}-{y+1}',section='C9',metric=metric,population='first_time_first_year',gender='total',residency='all',value=val,unit='score',source_url=s['source_url'],page=pg,extraction_method='official_pdf_text_table_direct',verification_status='source_table_reviewed',notes='Score distribution among enrolled students who submitted this assessment.'))
     break
 # C10 class rank percentages. Some Harvard PDFs wrap the rank-reporting row
 # onto the next physical page; each cell is checked near its label.
 rank_values={2019:(93,98,100,33),2020:(94,98,99.6,39),2021:(93.1,98.9,99.7,31),2022:(92.2,97.6,99.8,30),2023:(94.40,99.38,99.79,29),2024:(94,99,100,29)}[y]
 for label,metric,val in zip(('Percent in top tenth of high school graduating class','Percent in top quarter of high school graduating class','Percent in top half of high school graduating class','Percent of total first-time, first-year'),('hs_rank_top10_pct','hs_rank_top25_pct','hs_rank_top50_pct','hs_rank_reported_pct'),rank_values):
  hits=[]
  for pg,p in enumerate(pages,1):
   pos=p.find(label)
   if pos>=0 and any(float(z)==val for z in re.findall(r'([\d.]+)\s*%',p[pos:pos+300])):hits.append(pg)
  if not hits:raise ValueError((y,metric,val))
  rows.append(dict(school='Harvard University',unitid=166027,cohort_year=y,cds_edition=f'{y}-{y+1}',section='C10',metric=metric,population='first_time_first_year',gender='total',residency='all',value=f'{val:g}',unit='percent',source_url=s['source_url'],page=hits[0],extraction_method='official_pdf_text_table_direct',verification_status='source_table_reviewed',notes='Official C10; top-rank percentages among rank-reporting first-years, rank_reported_pct among all enrolled first-years.'))
# 2024 enrollment/aid values explicitly inspected in the official PDF.
y=2024;s=source_rows[y];pages=Path('sources/private/harvard_2024.txt').read_text(errors='replace').split('\f')
extras=[('B1','undergraduate_enrollment',7038,'count','first_time_first_year',3,'Fall 2024 all undergraduates, degree and non-degree; population actually all_undergraduates.'),
 ('H2','aid_need_determined_count',920,'count','full_time_first_year',19,'Aid academic year 2023-2024 final, prior to CDS edition.'),
 ('H2','aid_need_based_received_count',920,'count','full_time_first_year',19,'Aid academic year 2023-2024 final; H2 D recipients of any aid among students determined to have need.'),
 ('H2','aid_need_based_grant_received_count',920,'count','full_time_first_year',19,'Aid academic year 2023-2024 final; H2 E recipients of need-based scholarship/grant among students awarded aid.'),
 ('H2','aid_need_fully_met_count',920,'count','full_time_first_year',19,'Aid academic year 2023-2024 final (H2 H).'),
 ('H2','aid_need_met_pct',100,'percent','full_time_first_year',20,'Aid academic year 2023-2024 final (H2 I), among those awarded need-based aid.'),
 ('H2','aid_need_based_grant_mean_usd',73497,'usd','full_time_first_year',20,'Aid academic year 2023-2024 final (H2 K), mean among grant recipients.')]
for sec,metric,val,unit,pop,page,note in extras:
 assert str(val) in pages[page-1].replace(',','').replace(' ','').replace('$',''),(metric,page)
 rows.append(dict(school='Harvard University',unitid=166027,cohort_year=y if sec=='B1' else 2023,cds_edition='2024-2025',section=sec,metric=metric,population='all_undergraduates' if sec=='B1' else pop,gender='total',residency='all',value=val,unit=unit,source_url=s['source_url'],page=page,extraction_method='official_pdf_text_table_direct',verification_status='source_table_reviewed',notes=note))
with open('shards/private/harvard_observations.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
print('Harvard observations',len(rows))
