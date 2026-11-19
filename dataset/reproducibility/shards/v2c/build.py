"""Assemble manually table-reviewed v2c CDS observations; do not infer missing cells."""
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SHARD = BASE / 'shards/v2c'
SOURCE_COLUMNS = ['school','unitid','cohort_year','cds_edition','source_url','local_path','sha256','retrieved_at','format','status','notes']
OBS_COLUMNS = ['school','unitid','cohort_year','cds_edition','section','metric','population','gender','residency','value','unit','source_url','page','extraction_method','verification_status','notes']

# Each tuple: metric, value, physical PDF page, optional note. C1 total rows
# are taken from the published total column when present, not reconstructed.
DATA = {
 ('Bowdoin College','161004',2023): {
  'file':'raw/v2c/161004_2023.pdf','rows':[
   ('applicants',10966,15,''),('admitted',879,15,''),('enrolled',504,15,''),
   ('waitlist_admitted',29,16,'C2 offered/accepted marked N/A; not populated.'),
  ]},
 ('Carleton College','173258',2024): {
  'file':'raw/v2c/173258_2024.pdf','rows':[
   ('applicants',7133,8,''),('admitted',1456,8,''),('enrolled',507,8,''),
   ('waitlist_offered',573,8,''),('waitlist_accepted',242,8,''),('waitlist_admitted',52,8,''),
  ]},
 ('Middlebury College','230959',2023): {
  'file':'raw/v2c/230959_2023.pdf','rows':[
   ('applicants',13297,16,''),('admitted',1379,16,''),('enrolled',615,16,''),
   ('waitlist_offered',2778,17,''),
   ('waitlist_accepted',2734,17,'C2 explicitly labels this count Fall Only.'),
   ('waitlist_admitted',36,17,'C2 explicitly labels this count Fall Only.'),
  ]},
 ('Middlebury College','230959',2024): {
  'file':'raw/v2c/230959_2024.pdf','rows':[
   ('applicants',12540,7,''),
   ('admitted',1348,7,'C1 explicitly labels September Only.'),
   ('enrolled',598,7,'C1 explicitly labels September Only.'),
   ('waitlist_offered',2285,7,''),
   ('waitlist_accepted',2256,7,'C2 explicitly labels September Only.'),
   ('waitlist_admitted',45,7,'C2 explicitly labels September Only.'),
  ]},
 ('Claremont McKenna College','112260',2024): {
  'file':'raw/v2c/112260_2024.pdf','rows':[
   ('applicants',6529,7,''),('admitted',626,7,''),('enrolled',337,7,''),
   ('waitlist_offered',997,7,''),('waitlist_accepted',621,7,''),('waitlist_admitted',33,7,''),
  ]},
 ('Claremont McKenna College','112260',2023): {
  'file':'raw/v2c/112260_2023.pdf','rows':[
   ('applicants',5799,8,''),('admitted',645,8,''),('enrolled',321,8,''),
   ('waitlist_offered',591,8,''),('waitlist_accepted',396,8,''),('waitlist_admitted',44,8,''),
  ]},
 ('Harvey Mudd College','115409',2024): {
  'file':'raw/v2c/115409_2024.pdf','rows':[
   ('applicants',5094,10,''),('admitted',645,10,''),('enrolled',231,10,''),
   ('waitlist_offered',663,10,''),('waitlist_accepted',403,10,''),('waitlist_admitted',53,10,''),
  ]},
 ('Harvey Mudd College','115409',2023): {
  'file':'raw/v2c/115409_2023.pdf','rows':[
   ('applicants',4792,15,''),('admitted',626,15,''),('enrolled',224,15,''),
   ('waitlist_offered',604,16,''),('waitlist_accepted',406,16,''),('waitlist_admitted',57,16,''),
  ]},
 ('Amherst College','164465',2024): {
  'file':None,
  'rows':[
   ('applicants',13743,1,'Official PDF C1 residency total column; PDF rendered by web index at physical p1.'),
   ('admitted',1238,1,''),('enrolled',480,1,''),
   ('waitlist_offered',1105,1,''),('waitlist_accepted',623,1,''),('waitlist_admitted',8,1,''),
   ('sat_submit_pct',39,4,''),('act_submit_pct',22,4,''),
   ('sat_composite_p25',1500,4,''),('sat_composite_p50',1540,4,''),('sat_composite_p75',1560,4,''),
   ('sat_ebrw_p25',740,4,''),('sat_ebrw_p50',760,4,''),('sat_ebrw_p75',780,4,''),
   ('sat_math_p25',750,4,''),('sat_math_p50',780,4,''),('sat_math_p75',800,4,''),
   ('act_composite_p25',33,4,''),('act_composite_p50',34,4,''),('act_composite_p75',35,4,''),
  ]},
 ('Amherst College','164465',2023): {
  'file':None,
  'rows':[
   ('applicants',12727,1,''),('admitted',1250,1,''),('enrolled',488,1,''),
   ('waitlist_offered',924,2,''),('waitlist_accepted',599,2,''),('waitlist_admitted',47,2,''),
   ('sat_submit_pct',38,5,''),('act_submit_pct',17,5,''),
   ('sat_composite_p25',1480,5,''),('sat_composite_p50',1520,5,''),('sat_composite_p75',1550,5,''),
   ('sat_ebrw_p25',690,5,''),('sat_ebrw_p50',740,5,''),('sat_ebrw_p75',770,5,''),
   ('sat_math_p25',670,5,''),('sat_math_p50',760,5,''),('sat_math_p75',780,5,''),
   ('act_composite_p25',31,5,''),('act_composite_p50',33,5,''),('act_composite_p75',35,5,''),
  ]},
 ('Bowdoin College','161004',2024): {
  'file':'raw/v2c/161004_2024.pdf',
  'rows':[
   ('applicants',13265,12,''),('admitted',946,12,''),('enrolled',507,12,''),
   ('waitlist_admitted',22,12,'C2 offered/accepted cells are blank; only admitted is reported.'),
   ('sat_submit_pct',31.16,17,''),('act_submit_pct',16.77,17,''),
   ('sat_composite_p25',1470,17,''),('sat_composite_p50',1510,17,''),('sat_composite_p75',1540,17,''),
   ('sat_ebrw_p25',730,17,''),('sat_ebrw_p50',750,17,''),('sat_ebrw_p75',770,17,''),
   ('sat_math_p25',740,17,''),('sat_math_p50',770,17,''),('sat_math_p75',780,17,''),
   ('act_composite_p25',33,17,''),('act_composite_p50',34,17,''),('act_composite_p75',35,17,''),
  ]},
 ('Carleton College','173258',2023): {
  'file':'raw/v2c/173258_2023.pdf',
  'rows':[
   ('applicants',6464,20,''),('admitted',1440,20,''),('enrolled',538,20,''),
   ('waitlist_offered',782,20,''),('waitlist_accepted',356,20,''),('waitlist_admitted',35,20,''),
   ('sat_submit_pct',32,25,''),('act_submit_pct',28,25,''),
   ('sat_composite_p25',1440,25,''),('sat_composite_p50',1490,25,''),('sat_composite_p75',1530,25,''),
   ('sat_ebrw_p25',700,25,''),('sat_ebrw_p50',740,25,''),('sat_ebrw_p75',760,25,''),
   ('sat_math_p25',710,25,''),('sat_math_p50',760,25,''),('sat_math_p75',790,25,''),
   ('act_composite_p25',32,25,''),('act_composite_p50',33,25,''),('act_composite_p75',34,25,''),
  ]},
}

# C9 tuples: physical page; SAT%, ACT%; SAT composite 25/50/75;
# SAT EBRW 25/50/75; SAT math 25/50/75; ACT composite 25/50/75.
C9 = {
 ('112260',2023):(11,29,16,1470,1500,1530,710,740,770,740,770,790,33,34,35),
 ('112260',2024):(10,26,13,1490,1520,1550,720,750,770,750,780,790,33,34,35),
 ('115409',2023):(23,51,17,1490,1520,1550,720,750,770,760,780,790,34,35,36),
 ('115409',2024):(15,52,16,1510,1530,1560,730,750,770,770,790,800,34,35,36),
 ('161004',2023):(23,36.7,21.8,1470,1510,1530,730,750,760,750,760,790,33,34,35),
 ('173258',2024):(10,34,25,1470,1510,1540,720,750,770,730,770,790,32,34,35),
 ('230959',2023):(22,28,14,1440,1500,1530,720,740,770,710,750,780,33,34,34),
 ('230959',2024):(10,28,18,1450,1500,1530,720,740,760,725,760,790,33,34,35),
}
C9_METRICS = ('sat_submit_pct','act_submit_pct','sat_composite_p25','sat_composite_p50','sat_composite_p75','sat_ebrw_p25','sat_ebrw_p50','sat_ebrw_p75','sat_math_p25','sat_math_p50','sat_math_p75','act_composite_p25','act_composite_p50','act_composite_p75')
for (unitid,year), values in C9.items():
 for (school,u,y), item in DATA.items():
  if (u,y)!=(unitid,year): continue
  page,*numbers=values
  assert len(numbers)==len(C9_METRICS)
  note='School notes this count/percent covers students who did not apply test optional and submitted SAT/ACT.' if (unitid,year)==('230959',2023) else ''
  item['rows'].extend((metric,value,page,note if metric.endswith('_submit_pct') else '') for metric,value in zip(C9_METRICS,numbers))
  break
 else: raise AssertionError((unitid,year))

def section(metric):
 if metric.startswith('waitlist_'): return 'C2'
 if metric in ('applicants','admitted','enrolled'): return 'C1'
 if metric.startswith(('sat_','act_')): return 'C9'
 if metric.startswith('hs_rank_'): return 'C10'
 if metric.startswith('hs_gpa_'): return 'C12'
 raise ValueError(metric)

def write():
 candidates={(r['school'],int(r['cohort_year'])):r for r in csv.DictReader(open(SHARD/'source_candidates.csv'))}
 remote_receipts={}
 import json
 for manifest in (BASE/'raw/recovery/document_recovery.json',BASE/'raw/recovery2/document_recovery.json'):
  if not manifest.exists(): continue
  for receipt in json.loads(manifest.read_text()):
   if receipt.get('shard')=='v2c' and receipt.get('status')=='downloaded':
    remote_receipts[(receipt['unitid'],int(receipt['year']))]=receipt
 # Add manually reviewed observations only. Include all candidate URLs in the
 # source ledger so failed acquisition is not mistaken for absent research.
 source_rows=[]; obs_rows=[]
 for key,c in candidates.items():
  school,year=key
  item=DATA.get((school,c['unitid'],year))
  if item:
   path=item['file']
   digest=hashlib.sha256((BASE/path).read_bytes()).hexdigest() if path else ''
   receipt=remote_receipts.get((c['unitid'],year),{})
   retrieved=receipt.get('retrieved_at',c['retrieved_at']) if path else '2026-10-26T15:03:00+00:00'
   source_rows.append(dict(school=school,unitid=c['unitid'],cohort_year=year,cds_edition=c['cds_edition'],source_url=c['source_url'],local_path=path or '',sha256=digest,retrieved_at=retrieved,format='pdf',status='source_table_reviewed' if path else 'official_web_pdf_table_reviewed',notes='Official PDF; physical C1/C2 and C9 pages visually inspected.' if path else 'Official Amherst PDF rendered by web index with physical page markers, section headers and full tabular values; local GET returned HTTP 405, so no local binary/hash.'))
   for metric,value,page,note in item['rows']:
    obs_rows.append(dict(school=school,unitid=c['unitid'],cohort_year=year,cds_edition=c['cds_edition'],section=section(metric),metric=metric,population='first_time_first_year',gender='total',residency='all',value=value,unit='percent' if metric.endswith('_pct') else 'count' if metric in ('applicants','admitted','enrolled') or metric.startswith('waitlist_') else 'score',source_url=c['source_url'],page=page,extraction_method='manual_table_review' if path else 'official_web_pdf_rendered_table_review',verification_status='source_table_reviewed',notes=note))
  else:
   source_rows.append({k:c.get(k,'') for k in SOURCE_COLUMNS})
 for name,columns,rows in [('sources.csv',SOURCE_COLUMNS,source_rows),('observations.csv',OBS_COLUMNS,obs_rows)]:
  with open(SHARD/name,'w',newline='') as f:
   w=csv.DictWriter(f,columns);w.writeheader();w.writerows(rows)
 for key in DATA:
  m={r['metric']:int(r['value']) for r in obs_rows if (r['school'],r['unitid'],int(r['cohort_year']))==key and r['metric'] in ('applicants','admitted','enrolled')}
  assert m['applicants']>=m['admitted']>=m['enrolled']>=0,key
 print(f'{len(DATA)} school-years; {len(obs_rows)} observations')

if __name__=='__main__': write()
