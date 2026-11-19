"""Compile source-table-reviewed private-university CDS observations.

The table below is a transcription ledger of official C1 tables inspected on
2026-10-26. Harvard observations are independently extracted from six original
downloaded PDFs by extract_harvard.py. Never infer blank cells as zero.
"""
import csv
from pathlib import Path
from datetime import datetime, timezone

BASE = Path('shards/private')
COLS = 'school unitid cohort_year cds_edition section metric population gender residency value unit source_url page extraction_method verification_status notes'.split()
SCOLS = 'school unitid cohort_year cds_edition source_url local_path sha256 retrieved_at format status notes'.split()
ROOT = Path('sources/private')

# school, UNITID, year, official URL, C1 PDF physical page (or HTML selector),
# C1 applicants/admitted/enrolled, C2 page and values, method, source caveat.
SPECS = [
 ('Yale University',130794,2023,'https://oir.yale.edu/sites/default/files/cds_yale_2023-24_vf_20240320.pdf','8',(51803,2332,1641),'9',(1145,899,0),'derived_sum_of_reported_categories','C1 gender categories summed; original table inspected. Do not use OCR artifact 7889 for male enrollment.'),
 ('Yale University',130794,2024,'https://oir.yale.edu/sites/default/files/yale_cds_2024-25_rmd_20250612.pdf','9',(57517,2227,1554),'10',(773,565,23),'derived_sum_of_reported_categories','C1 gender categories summed; original table inspected; unknown and another-gender applicant categories included.'),
 ('Princeton University',186131,2023,'https://registrar.princeton.edu/sites/g/files/toruqf136/files/documents/CDS_2023-2024.pdf','C1 (physical page unverified)',(39644,1782,1366),'C2 (physical page unverified)',(1302,1032,52),'official_pdf_indexed_table_direct','Official PDF C1 direct totals; physical page not independently established.'),
 ('Princeton University',186131,2024,'https://ir.princeton.edu/sites/g/files/toruqf2041/files/documents/CDS_2425_Princeton_v2.pdf','8',(40468,1868,1410),'9',(1734,1396,40),'official_pdf_indexed_table_direct','Official PDF C1 residency table direct totals; gender breakdown corroborates.'),
 ('Massachusetts Institute of Technology',166683,2023,'https://ir.mit.edu/projects/2023-24-common-data-set/','C1 HTML',(26914,1291,1092),'C2 HTML',(619,558,32),'official_html_table_direct','MIT note: admissions classification methodology and numbers revised in February 2025.'),
 ('Massachusetts Institute of Technology',166683,2024,'https://ir.mit.edu/projects/2024-25-common-data-set/','C1 HTML',(28232,1284,1106),'C2 HTML',(590,509,9),'official_html_table_direct','Official MIT HTML C1 table.'),
 ('Stanford University',243744,2023,'https://drive.google.com/file/d/11t0SaMg7GHtBV_rAz82AqbLWLFkI5--H/view','C1 (printed p9; physical page unverified)',(53733,2099,1699),'C2 (printed p9; physical page unverified)',(607,506,76),'derived_sum_of_reported_categories','Official Stanford Drive CDS; men+women categories; physical page to verify. See source evidence text.'),
 ('Stanford University',243744,2024,'https://drive.google.com/file/d/12MjIqdzzHiECf6hfRlbU3RmmIy14hl1H/view','10',(57326,2067,1693),'10',(483,414,25),'official_drive_pdf_table_direct','Official Stanford Drive CDS; printed p8, physical p10.'),
 ('Columbia University',190150,2023,'https://opir.columbia.edu/sites/opir.columbia.edu/files/content/Common%20Data%20Set/2023-24_Columbia_College_and_Columbia_Engineering_CDS.pdf','10',(57126,2284,1454),'C2 (physical page unverified)',None,'official_pdf_indexed_table_direct','Columbia College and Columbia Engineering only; excludes School of General Studies. Not institution-wide IPEDS denominator.'),
 ('Columbia University',190150,2024,'https://opir.columbia.edu/sites/opir.columbia.edu/files/content/Common%20Data%20Set/2024-25_Columbia_College_and_Columbia_Engineering_CDS.pdf','10',(60247,2325,1483),'C2 (physical page unverified)',None,'official_pdf_indexed_table_direct','Columbia College and Columbia Engineering only; excludes School of General Studies. Not institution-wide IPEDS denominator.'),
 ('Cornell University',190415,2023,'https://irp.cornell.edu/wp-content/uploads/2024/08/CDS_UNL2_2023_2024-v11.pdf','19',(67846,5358,3537),'19',(8282,6166,362),'official_pdf_indexed_table_direct','Official v11 PDF C1 residency totals on physical p19; gender sums concur.'),
 ('Cornell University',190415,2024,'https://irp.dpb.cornell.edu/wp-content/uploads/2025/02/CDS-2024-2025-v1.pdf','C1 (physical page unverified)',(65612,5516,3525),'C2 (physical page unverified)',(8103,6190,388),'official_pdf_indexed_table_direct','Official v1 PDF C1; later v6 linked by Cornell has blank C1/C2. Version conflict retained, physical page unverified.'),
 ('Brown University',217156,2024,'https://oir.brown.edu/sites/default/files/2020-04/CDS_2024_2025.pdf','C1 (physical page unverified)',(48904,2638,1719),'C2 (physical page unverified)',None,'derived_sum_of_reported_categories','Official Brown PDF search-index table; gender categories summed; physical page unverified.'),
 ('Dartmouth College',182670,2024,'https://www.dartmouth.edu/oir/pdfs/cds_2024-2025.pdf','C1 (physical page unverified)',(31656,1710,1182),'C2 (physical page unverified)',(2589,2189,29),'official_pdf_indexed_table_direct','Official PDF C1 residency table direct totals; physical page unverified.'),
 ('Duke University',198419,2023,'https://ir.provost.duke.edu/sites/default/files/CDS-2023-24-FINAL-2.pdf','11',(46366,3145,1742),'11',(2266,None,None),'official_pdf_indexed_table_direct','Official Duke PDF C1 physical p11, residency totals direct; C2 accepted/admitted blank, omitted.'),
 ('Northwestern University',147767,2023,'https://www.enrollment.northwestern.edu/data/2023-2024.pdf','C1 (physical page unverified)',(51769,3739,2111),'C2 (physical page unverified)',(None,None,55),'derived_sum_of_reported_categories','Official PDF C1 reported gender categories summed; waitlist offered/accepted suppressed, omitted.'),
 ('Northwestern University',147767,2024,'https://enrollment.northwestern.edu/data/2024-2025.pdf','C1 (physical page unverified)',(49474,3806,2105),'C2 (physical page unverified)',(None,None,59),'derived_sum_of_reported_categories','Official PDF C1 reported gender categories summed. B1 first-year gender counts differ by one from C1, total agrees; waitlist offered/accepted suppressed.'),
]

rows=list(csv.DictReader(open(BASE/'harvard_observations.csv',newline='')))
manifest=[r for r in csv.DictReader(open(BASE/'sources.csv',newline='')) if r['school']=='Harvard University']
for school,unitid,year,url,page,totals,c2page,c2,method,note in SPECS:
 assert totals[0]>=totals[1]>=totals[2]>0,(school,year,totals)
 edition=f'{year}-{year+1}'
 for metric,value in zip(('applicants','admitted','enrolled'),totals):
  rows.append(dict(school=school,unitid=unitid,cohort_year=year,cds_edition=edition,section='C1',metric=metric,population='first_time_first_year',gender='total',residency='all',value=value,unit='count',source_url=url,page=page,extraction_method=method,verification_status='source_table_reviewed',notes=note))
 if c2:
  for metric,value in zip(('waitlist_offered','waitlist_accepted','waitlist_admitted'),c2):
   if value is not None:
    rows.append(dict(school=school,unitid=unitid,cohort_year=year,cds_edition=edition,section='C2',metric=metric,population='first_time_first_year',gender='total',residency='all',value=value,unit='count',source_url=url,page=c2page,extraction_method=method,verification_status='source_table_reviewed',notes=note))
 manifest.append(dict(school=school,unitid=unitid,cohort_year=year,cds_edition=edition,source_url=url,local_path='',sha256='',retrieved_at=datetime.now(timezone.utc).isoformat(),format='html' if 'mit.edu/projects/' in url else 'pdf',status='official_source_table_reviewed_via_web_index' if 'drive.google.com' not in url else 'official_drive_connector_table_reviewed',notes=note))

def add(school,year,section,metric,value,unit,page,pop='first_time_first_year',note='Official CDS table inspected.'):
 s=next(x for x in SPECS if x[0]==school and x[2]==year)
 rows.append(dict(school=school,unitid=s[1],cohort_year=year,cds_edition=f'{year}-{year+1}',section=section,metric=metric,population=pop,gender='total',residency='all',value=value,unit=unit,source_url=s[3],page=page,extraction_method='official_source_table_direct',verification_status='source_table_reviewed',notes=note))

for metric,value in [('sat_submit_pct',61),('act_submit_pct',25)]:add('Yale University',2024,'C9',metric,value,'percent','13')
for base,vals in [('sat_composite',(1480,1530,1560)),('sat_ebrw',(730,760,780)),('sat_math',(740,780,790)),('act_composite',(33,34,35))]:
 for suffix,value in zip(('p25','p50','p75'),vals):add('Yale University',2024,'C9',f'{base}_{suffix}',value,'score','13')
for metric,value in [('sat_submit_pct',50.3),('act_submit_pct',19.0)]:add('Stanford University',2024,'C9',metric,value,'percent','13')
for base,vals in [('sat_composite',(1510,1540,1570)),('sat_ebrw',(740,760,780)),('sat_math',(770,790,800)),('act_composite',(34,35,35))]:
 for suffix,value in zip(('p25','p50','p75'),vals):add('Stanford University',2024,'C9',f'{base}_{suffix}',value,'score','13')
for metric,value in [('sat_submit_pct',42),('act_submit_pct',14)]:add('Cornell University',2023,'C9',metric,value,'percent','25')
for base,vals in [('sat_composite',(1480,1520,1550)),('sat_ebrw',(720,740,770)),('sat_math',(760,780,790)),('act_composite',(33,34,35))]:
 for suffix,value in zip(('p25','p50','p75'),vals):add('Cornell University',2023,'C9',f'{base}_{suffix}',value,'score','25')
add('Stanford University',2024,'B1','undergraduate_enrollment',7904,'count','B1 (physical page unverified)','all_undergraduates','Official Stanford B1 all undergraduate students, Fall 2024.')
add('Princeton University',2024,'B1','undergraduate_enrollment',5813,'count','3','all_undergraduates','Official Princeton B1 total undergraduate students, Fall 2024.')
add('Cornell University',2023,'B1','undergraduate_enrollment',16071,'count','7','all_undergraduates','Official Cornell B1 all undergraduate students, Fall 2023, including non-degree seeking.')
for school,year,page,vals in [
 ('Yale University',2024,'14',(96,99,100,33)),
 ('Cornell University',2023,'27',(81.7,94.5,99.5,17.3)),
]:
 for metric,value in zip(('hs_rank_top10_pct','hs_rank_top25_pct','hs_rank_top50_pct','hs_rank_reported_pct'),vals):
  add(school,year,'C10',metric,value,'percent',page,'first_time_first_year','Official C10 high-school class-rank table; percentages are among students reporting rank, except rank_reported_pct denominator is all enrolled first-years.')
add('Princeton University',2024,'C12','hs_gpa_mean',3.95,'gpa','12','first_time_first_year','Official Princeton C12 reports 3.95 mean high-school GPA for enrolled first-years who submitted GPA; 99.3% submitted.')

# H2 must use the aid year indicated at H1, not blindly the CDS edition year.
for metric,value,unit in [('aid_need_determined_count',908,'count'),('aid_need_based_received_count',908,'count'),('aid_need_based_grant_received_count',905,'count'),('aid_need_fully_met_count',908,'count'),('aid_need_met_pct',100,'percent'),('aid_need_based_grant_mean_usd',74040,'usd')]:
 add('Yale University',2024,'H2',metric,value,unit,'27','full_time_first_year','H1 selects 2024-2025 estimated; H2 C/D/H/I/K respectively. Full-time first-year aid cohort 2024.')
for metric,value,unit,page in [('aid_need_determined_count',1735,'count','57'),('aid_need_based_received_count',1735,'count','57'),('aid_need_based_grant_received_count',1697,'count','57'),('aid_need_fully_met_count',1735,'count','58'),('aid_need_met_pct',100,'percent','58'),('aid_need_based_grant_mean_usd',59302,'usd','58')]:
 add('Cornell University',2023,'H2',metric,value,unit,page,'full_time_first_year','H1 selects 2023-2024 estimated; H2 C/D/H/I/K respectively. Full-time first-year aid cohort 2023.')

# C1 sex/gender cells are included only when the official row values were seen.
# The final tuple maps to the PDF's male, female, another-gender, unknown columns.
GENDER_ROWS = {
 ('Yale University',2024): {'applicants':(24951,32540,20,6),'admitted':(1136,1091,None,None),'enrolled':(782,772,None,None)},
 ('Princeton University',2024): {'applicants':(20563,19883,22,None),'enrolled':(693,717,None,None)},
 ('Stanford University',2024): {'applicants':(29602,27724,None,None),'admitted':(1015,1052,None,None),'enrolled':(835,858,None,None)},
 ('Columbia University',2023): {'applicants':(23720,32219,1187,None),'admitted':(1087,1142,55,None),'enrolled':(694,728,32,None)},
 ('Columbia University',2024): {'applicants':(26575,32668,1004,None),'admitted':(1082,1191,52,None),'enrolled':(688,767,28,None)},
 ('Cornell University',2023): {'applicants':(33674,34172,None,None),'admitted':(2459,2899,None,None),'enrolled':(1643,1894,None,None)},
 ('Brown University',2024): {'applicants':(18960,29917,27,None),'admitted':(1326,1309,3,None),'enrolled':(855,863,None,1)},
 ('Duke University',2023): {'applicants':(21533,24800,None,None),'admitted':(1463,1682,None,None),'enrolled':(791,951,None,None)},
 ('Northwestern University',2023): {'applicants':(24511,27256,2,None),'admitted':(1729,2010,0,None),'enrolled':(965,1144,2,None)},
 ('Northwestern University',2024): {'applicants':(23774,25686,14,None),'admitted':(1735,2070,1,None),'enrolled':(977,1127,1,None)},
}
for (school,year),metric_data in GENDER_ROWS.items():
 spec=next(s for s in SPECS if s[0]==school and s[2]==year)
 for metric,vals in metric_data.items():
  total=spec[5][('applicants','admitted','enrolled').index(metric)]
  assert sum(v for v in vals if v is not None)<=total,(school,year,metric,vals,total)
  for gender,value in zip(('male','female','another_gender','unknown'),vals):
   if value is None:continue
   rows.append(dict(school=school,unitid=spec[1],cohort_year=year,cds_edition=f'{year}-{year+1}',section='C1',metric=metric,population='first_time_first_year',gender=gender,residency='all',value=value,unit='count',source_url=spec[3],page=spec[4],extraction_method='official_source_table_direct',verification_status='source_table_reviewed',notes='Reported C1 gender cell; missing categories omitted. '+spec[9]))

# C1 residency cells (reported directly; totals preserved as separate rows).
RESIDENCY_ROWS = {
 ('Duke University',2023): {'applicants':(3765,32191,10410),'admitted':(376,2370,399),'enrolled':(118,1429,195)},
 ('Cornell University',2023): {'applicants':(12606,38401,16839),'admitted':(1523,3357,478),'enrolled':(1148,2031,358)},
}
for (school,year),metric_data in RESIDENCY_ROWS.items():
 spec=next(s for s in SPECS if s[0]==school and s[2]==year)
 for metric,vals in metric_data.items():
  assert sum(vals)==spec[5][('applicants','admitted','enrolled').index(metric)]
  for residence,value in zip(('in_state','out_of_state','international'),vals):
   rows.append(dict(school=school,unitid=spec[1],cohort_year=year,cds_edition=f'{year}-{year+1}',section='C1',metric=metric,population='first_time_first_year',gender='total',residency=residence,value=value,unit='count',source_url=spec[3],page=spec[4],extraction_method='official_source_table_direct',verification_status='source_table_reviewed',notes='Official C1 residency table; totals sum exactly. '+spec[9]))

assert all(set(r)==set(COLS) for r in rows)
with open(BASE/'observations.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(rows)
with open(BASE/'sources.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=SCOLS);w.writeheader();w.writerows(manifest)
print('rows',len(rows),'school-years',len({(r['school'],r['cohort_year']) for r in rows if r['section']=='C1'}),'schools',len({r['school'] for r in rows if r['section']=='C1'}))
