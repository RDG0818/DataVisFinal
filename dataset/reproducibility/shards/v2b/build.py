"""Reviewed official CDS transcription for v2b. Re-run after editing ENTRIES."""
import csv
import hashlib
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OBS = ['school','unitid','cohort_year','cds_edition','section','metric','population','gender','residency','value','unit','source_url','page','extraction_method','verification_status','notes']
SRC = ['school','unitid','cohort_year','cds_edition','source_url','local_path','sha256','retrieved_at','format','status','notes']

# Every tuple was read in the named section of the university-hosted CDS PDF.
# Metric tuple: (section, name, value, physical one-based page, unit).
ENTRIES = [
    ('University of Washington-Seattle Campus',236948,2023,
     'https://finance.uw.edu/iads/files/docs/ipeds/common_data_set/cds_seattle_2023_2024.xlsx',
     'UW official Seattle-campus XLSX linked from its CDS index. Published C1 residency totals include applicants/admittees/enrollees not in the binary sex rows; use explicit totals. C2 rows explicit.',
     [('C1','applicants',62428,'CDS-C!E20','count'),('C1','admitted',26552,'CDS-C!E21','count'),('C1','enrolled',7006,'CDS-C!E22','count'),
      ('C2','waitlist_offered',7915,'CDS-C!B32','count'),('C2','waitlist_accepted',4122,'CDS-C!B33','count'),('C2','waitlist_admitted',2985,'CDS-C!B34','count')]),
    ('University of Washington-Seattle Campus',236948,2024,
     'https://finance.uw.edu/iads/files/docs/ipeds/common_data_set/cds_2024-2025_seattle.pdf',
     'UW official Seattle-campus PDF linked from its CDS index. C1 totals on PDF p14 equal the four reported gender categories on p13; C2 on p14. Original rendered PDF was visually inspected because text extraction omitted filled values.',
     [('C1','applicants',69166,14,'count'),('C1','admitted',27076,14,'count'),('C1','enrolled',7195,14,'count'),
      ('C2','waitlist_offered',15591,14,'count'),('C2','waitlist_accepted',7983,14,'count'),('C2','waitlist_admitted',1596,14,'count')]),
    ('University of Maryland-College Park',163286,2023,
     'https://www.irpa.umd.edu/InstitutionalData/CommonDataSet/CDS_2023-2024.xlsx',
     'UMD College Park official CDS workbook. C1 totals explicitly published in CDS-C residency table; gender sums match. C2 zero acceptances/admissions are explicit source values.',
     [('C1','applicants',59369,'CDS-C!E20','count'),('C1','admitted',26623,'CDS-C!E21','count'),('C1','enrolled',6197,'CDS-C!E22','count'),
      ('C2','waitlist_offered',290,'CDS-C!B32','count'),('C2','waitlist_accepted',0,'CDS-C!B33','count'),('C2','waitlist_admitted',0,'CDS-C!B34','count')]),
    ('University of Maryland-College Park',163286,2024,
     'https://www.irpa.umd.edu/InstitutionalData/CommonDataSet/CDS_2024-2025.xlsx',
     'UMD College Park official CDS workbook. C1 totals explicitly published in CDS-C residency table and match gender sums. C2 zero acceptances/admissions are explicit source values.',
     [('C1','applicants',60042,'CDS-C!E37','count'),('C1','admitted',26897,'CDS-C!E38','count'),('C1','enrolled',5818,'CDS-C!E39','count'),
      ('C2','waitlist_offered',250,'CDS-C!E52','count'),('C2','waitlist_accepted',0,'CDS-C!E53','count'),('C2','waitlist_admitted',0,'CDS-C!E54','count')]),
    ('Ohio State University-Main Campus',204796,2024,
     'https://irp.osu.edu/media/276',
     'Official Columbus-campus CDS PDF linked from OSU IRP. C1 published totals on p14 match men+women on p13. C2 waitlist offered zero is explicitly printed; acceptance/admission cells are blank and omitted. Original rendered PDF was visually inspected because text extraction omitted filled values.',
     [('C1','applicants',72829,14,'count'),('C1','admitted',44116,14,'count'),('C1','enrolled',9607,14,'count'),
      ('C2','waitlist_offered',0,14,'count')]),
    ('The University of Texas at Austin',228778,2023,
     'https://utexas.box.com/s/pt3l6ddqhi3ao8mr6ij7698dnx33otyf',
     'UT Austin official CDS linked from reports.utexas.edu; C1 published residency totals independently equal gender-category sums. C2 policy No, so blank waitlist counts omitted.',
     [('C1','applicants',66109,10,'count'),('C1','admitted',19253,10,'count'),('C1','enrolled',9385,10,'count')]),
    ('The University of Texas at Austin',228778,2024,
     'https://utexas.app.box.com/s/d9izqb6s8dw2xxg5h5sunxyhrnef2ay6',
     'UT Austin official CDS linked from reports.utexas.edu; C1 published residency totals independently equal gender-category sums. C2 waitlist count fields are blank.',
     [('C1','applicants',72885,8,'count'),('C1','admitted',19417,8,'count'),('C1','enrolled',9210,8,'count')]),
    ('University of Wisconsin-Madison',240444,2023,
     'https://uwmadison.app.box.com/s/50d3gbh8j6fltsphaxbqh7vpn0g4bdj0',
     'Wisconsin Madison official CDS university Box PDF; C1 totals are the published residency totals and equal the gender sums. C2 waitlist totals are explicit.',
     [('C1','applicants',63537,20,'count'),('C1','admitted',27527,20,'count'),('C1','enrolled',7966,20,'count'),
      ('C2','waitlist_offered',13364,20,'count'),('C2','waitlist_accepted',7221,20,'count'),('C2','waitlist_admitted',4436,20,'count')]),
    ('University of Wisconsin-Madison',240444,2024,
     'https://uwmadison.app.box.com/s/cm3r7gc83w3eqjotfbva111dnin6toer',
     'Wisconsin Madison official CDS university Box PDF. C1 residency table is unfilled and displays formula-generated zeros; C1 totals are derived from the explicit men+women+another+unknown gender table on p13: applicants 32863+33050+20+0, admitted 13835+15940+9+0, enrolled 3779+4734+1+0. C2 counts explicit on p14.',
     [('C1','applicants',65933,13,'count'),('C1','admitted',29784,13,'count'),('C1','enrolled',8514,13,'count'),
      ('C2','waitlist_offered',12584,14,'count'),('C2','waitlist_accepted',7644,14,'count'),('C2','waitlist_admitted',493,14,'count')]),
    ('Purdue University-Main Campus',243780,2023,
     'https://www.purdue.edu/idata/wp-content/uploads/2026/04/CDS_2023_2024.xlsx',
     'Official Purdue CDS-C workbook for Fall 2023, West Lafayette only. C1 published residency totals equal gender sums. Fall 2023 CDS enrolled 9,285 differs from IPEDS; preserved without substitution. C9 workbook fractions converted to percentages, rounded to two decimals.',
     [('C1','applicants',72800,'CDS-C!E30','count'),('C1','admitted',36602,'CDS-C!E31','count'),('C1','enrolled',9285,'CDS-C!E32','count'),
      ('C2','waitlist_offered',14184,'CDS-C!B42','count'),('C2','waitlist_accepted',5252,'CDS-C!B43','count'),('C2','waitlist_admitted',466,'CDS-C!B44','count'),
      ('C9','sat_submit_pct',72.64,'CDS-C!B177','percent'),('C9','act_submit_pct',23.60,'CDS-C!B178','percent'),
      ('C9','sat_composite_p25',1210,'CDS-C!B183','score'),('C9','sat_composite_p75',1450,'CDS-C!D183','score'),
      ('C9','sat_ebrw_p25',590,'CDS-C!B184','score'),('C9','sat_ebrw_p75',710,'CDS-C!D184','score'),
      ('C9','sat_math_p25',600,'CDS-C!B185','score'),('C9','sat_math_p75',760,'CDS-C!D185','score'),
      ('C9','act_composite_p25',27,'CDS-C!B186','score'),('C9','act_composite_p75',34,'CDS-C!D186','score')]),
    ('Purdue University-Main Campus',243780,2024,
     'https://www.purdue.edu/idata/wp-content/uploads/2026/04/CDS_2024-2025.xlsx',
     'Official Purdue CDS-C workbook for Fall 2024 covers West Lafayette plus Indianapolis plus Polytechnic Statewide, unlike earlier years. Source inconsistency: C1 admitted printed total CDS-C!C42=30,272, while gender CDS-C!C22:C23=22,551+16,721 and residency CDS-C!D42:F42=9,091+25,935+4,246 each sum to 39,272. Primary admitted preserves printed total; alternative sum is a separate metric pending editorial review. C9 workbook fractions converted to percentages, rounded to two decimals.',
     [('C1','applicants',78745,'CDS-C!C41','count'),('C1','admitted',30272,'CDS-C!C42','count'),('C1','admitted_sum_of_reported_categories',39272,'CDS-C!C22:C23,D42:F42','count'),('C1','enrolled',11467,'CDS-C!C43','count'),
      ('C2','waitlist_offered',3344,'CDS-C!C53','count'),('C2','waitlist_accepted',1860,'CDS-C!C54','count'),('C2','waitlist_admitted',9,'CDS-C!C55','count'),
      ('C9','sat_submit_pct',79.31,'CDS-C!C195','percent'),('C9','act_submit_pct',25.34,'CDS-C!C196','percent'),
      ('C9','sat_composite_p25',1210,'CDS-C!C202','score'),('C9','sat_composite_p75',1470,'CDS-C!E202','score'),
      ('C9','sat_ebrw_p25',600,'CDS-C!C203','score'),('C9','sat_ebrw_p75',720,'CDS-C!E203','score'),
      ('C9','sat_math_p25',600,'CDS-C!C204','score'),('C9','sat_math_p75',760,'CDS-C!E204','score'),
      ('C9','act_composite_p25',27,'CDS-C!C205','score'),('C9','act_composite_p75',34,'CDS-C!E205','score')]),
    ('Auburn University',100858,2023,
     'https://ir.auburn.edu/common-data-set/2023/section-c.php',
     'Official Auburn institutional research HTML CDS section C. C1 published aggregate totals include applicants not classified in men/women detail. C2 policy No; blank counts omitted.',
     [('C1','applicants',48179,'HTML:C1','count'),('C1','admitted',24315,'HTML:C1','count'),('C1','enrolled',5935,'HTML:C1','count'),
      ('C9','sat_submit_pct',18,'HTML:C9','percent'),('C9','act_submit_pct',76,'HTML:C9','percent'),
      ('C9','sat_composite_p25',1240,'HTML:C9','score'),('C9','sat_composite_p75',1360,'HTML:C9','score'),
      ('C9','sat_ebrw_p25',620,'HTML:C9','score'),('C9','sat_ebrw_p75',680,'HTML:C9','score'),
      ('C9','sat_math_p25',610,'HTML:C9','score'),('C9','sat_math_p75',690,'HTML:C9','score'),
      ('C9','act_composite_p25',25,'HTML:C9','score'),('C9','act_composite_p75',31,'HTML:C9','score'),
      ('C10','hs_rank_top10_pct',37,'HTML:C10','percent'),('C10','hs_rank_top25_pct',68,'HTML:C10','percent'),
      ('C10','hs_rank_top50_pct',93,'HTML:C10','percent'),('C10','hs_rank_reported_pct',34,'HTML:C10','percent')]),
    ('Auburn University',100858,2024,
     'https://ir.auburn.edu/common-data-set/2024/section-c.php',
     'Official Auburn institutional research HTML CDS section C. C1 published aggregate totals include applicants not classified in men/women detail. C2 policy No; blank counts omitted.',
     [('C1','applicants',55056,'HTML:C1','count'),('C1','admitted',25284,'HTML:C1','count'),('C1','enrolled',6103,'HTML:C1','count'),
      ('C9','sat_submit_pct',16,'HTML:C9','percent'),('C9','act_submit_pct',76,'HTML:C9','percent'),
      ('C9','sat_composite_p25',1260,'HTML:C9','score'),('C9','sat_composite_p75',1380,'HTML:C9','score'),
      ('C9','sat_ebrw_p25',630,'HTML:C9','score'),('C9','sat_ebrw_p75',690,'HTML:C9','score'),
      ('C9','sat_math_p25',620,'HTML:C9','score'),('C9','sat_math_p75',700,'HTML:C9','score'),
      ('C9','act_composite_p25',26,'HTML:C9','score'),('C9','act_composite_p75',31,'HTML:C9','score'),
      ('C10','hs_rank_top10_pct',35,'HTML:C10','percent'),('C10','hs_rank_top25_pct',67,'HTML:C10','percent'),
      ('C10','hs_rank_top50_pct',93,'HTML:C10','percent'),('C10','hs_rank_reported_pct',42,'HTML:C10','percent'),
      ('C12','hs_gpa_mean',4.09,'HTML:C12','gpa')]),
    ('University of Minnesota-Twin Cities',174066,2024,
     'https://idr.umn.edu/sites/idr.umn.edu/files/cds_2024_2025_tc_2.pdf',
     'Official Twin Cities campus CDS. C1 total residency row includes 5,769 applicants and 4,419 admits with unknown residency; sex categories independently sum to totals.',
     [('C1','applicants',41496,12,'count'),('C1','admitted',33091,12,'count'),('C1','enrolled',7391,12,'count')]),
    ('Rutgers University-New Brunswick',186380,2023,
     'https://oirapapps.rutgers.edu/CDS/2023/New%20Brunswick%20CDS_2023-2024_final_V1.pdf',
     'Rutgers New Brunswick campus official CDS, published August 2024. C1 totals equal gender and residency rows. C2 waitlist policy No; blank counts omitted.',
     [('C1','applicants',43347,5,'count'),('C1','admitted',28326,5,'count'),('C1','enrolled',7681,5,'count')]),
    ('University of Massachusetts-Amherst',166629,2023,
     'https://www.umass.edu/uair/sites/default/files/2024-07/common_data_set.pdf',
     'UMass Amherst official 2023-24 CDS. C1 totals independently equal the published gender category sums.',
     [('C1','applicants',50424,9,'count'),('C1','admitted',29129,9,'count'),('C1','enrolled',5286,9,'count'),
      ('C2','waitlist_offered',11588,9,'count'),('C2','waitlist_accepted',6628,9,'count'),('C2','waitlist_admitted',1701,9,'count'),
      ('C9','sat_submit_pct',27,12,'percent'),('C9','act_submit_pct',3.9,12,'percent'),
      ('C9','sat_composite_p25',1310,13,'score'),('C9','sat_composite_p75',1460,13,'score'),
      ('C9','sat_ebrw_p25',650,13,'score'),('C9','sat_ebrw_p75',720,13,'score'),
      ('C9','sat_math_p25',650,13,'score'),('C9','sat_math_p75',760,13,'score'),
      ('C9','act_composite_p25',29,13,'score'),('C9','act_composite_p75',33,13,'score'),
      ('C10','hs_rank_top10_pct',31.9,14,'percent'),('C10','hs_rank_top25_pct',67.3,14,'percent'),
      ('C10','hs_rank_top50_pct',93.4,14,'percent'),('C10','hs_rank_reported_pct',28.9,14,'percent'),
      ('C12','hs_gpa_mean',4.07,15,'gpa')]),
    ('Texas A&M University-College Station',228723,2023,
     'https://abpa.tamu.edu/_files/_documents/common-data/texas-a-m-commondataset-2023-2024updated.pdf',
     'Texas A&M College Station official CDS; C1 totals from published men/women table, confirmed by in-state/out-of-state/international table. C2 waitlist policy no; blanks omitted.',
     [('C1','applicants',51108,11,'count'),('C1','admitted',32249,11,'count'),('C1','enrolled',13721,11,'count')]),
    ('University of Illinois Urbana-Champaign',145637,2023,
     'https://uofi.box.com/shared/static/zaag0tgnyw34tt8vvai5mtacq9njj7pt.xlsx',
     'Illinois official DAIR CDS link; C1 totals in CDS-C residency table equal men+women+another gender rows. No IPEDS substitution.',
     [('C1','applicants',67398,'CDS-C!E20','count'),('C1','admitted',29446,'CDS-C!E21','count'),('C1','enrolled',8325,'CDS-C!E22','count'),
      ('C2','waitlist_offered',3073,'CDS-C!B32','count'),('C2','waitlist_accepted',1881,'CDS-C!B33','count'),('C2','waitlist_admitted',56,'CDS-C!B34','count'),
      ('C9','sat_submit_pct',40.4,'CDS-C!B153','percent'),('C9','act_submit_pct',16,'CDS-C!B154','percent'),
      ('C9','sat_composite_p25',1350,'CDS-C!B159','score'),('C9','sat_composite_p75',1510,'CDS-C!D159','score'),
      ('C9','sat_ebrw_p25',660,'CDS-C!B160','score'),('C9','sat_ebrw_p75',740,'CDS-C!D160','score'),
      ('C9','sat_math_p25',680,'CDS-C!B161','score'),('C9','sat_math_p75',790,'CDS-C!D161','score'),
      ('C9','act_composite_p25',30,'CDS-C!B162','score'),('C9','act_composite_p75',34,'CDS-C!D162','score'),
      ('C10','hs_rank_top10_pct',54,'CDS-C!B201','percent'),('C10','hs_rank_top25_pct',86,'CDS-C!B202','percent'),
      ('C10','hs_rank_top50_pct',98,'CDS-C!B203','percent'),('C10','hs_rank_reported_pct',24,'CDS-C!B206','percent')]),
    ('University of Illinois Urbana-Champaign',145637,2024,
     'https://uofi.box.com/shared/static/1m3p4sedkotywoec55zbnodc4oci5ctf.xlsx',
     'Illinois official DAIR CDS link; C1 totals explicitly reported at C49:C51 and match gender+unknown and residency subtotals.',
     [('C1','applicants',73742,'CDS-C!C49','count'),('C1','admitted',31247,'CDS-C!C50','count'),('C1','enrolled',9008,'CDS-C!C51','count'),
      ('C2','waitlist_offered',2794,'CDS-C!C91','count'),('C2','waitlist_accepted',1874,'CDS-C!C92','count'),('C2','waitlist_admitted',1,'CDS-C!C93','count'),
      ('C9','sat_submit_pct',41.28,'CDS-C!C262','percent'),('C9','act_submit_pct',14.33,'CDS-C!C263','percent'),
      ('C9','sat_composite_p25',1390,'CDS-C!C275','score'),('C9','sat_composite_p75',1520,'CDS-C!C277','score'),
      ('C9','sat_ebrw_p25',680,'CDS-C!C279','score'),('C9','sat_ebrw_p75',750,'CDS-C!C281','score'),
      ('C9','sat_math_p25',700,'CDS-C!C283','score'),('C9','sat_math_p75',790,'CDS-C!C285','score'),
      ('C9','act_composite_p25',30,'CDS-C!C288','score'),('C9','act_composite_p75',34,'CDS-C!C290','score')]),
    ('Ohio State University-Main Campus',204796,2023,
     'https://irp.osu.edu/sites/default/files/documents/2024/08/CDS_2023-2024-Columbus.pdf',
     'Official Ohio State Columbus campus CDS; C1 totals also equal reported gender sums. Do not combine with other OSU campuses.',
     [('C1','applicants',70028,14,'count'),('C1','admitted',35588,14,'count'),('C1','enrolled',8062,14,'count'),
      ('C2','waitlist_offered',2596,15,'count'),('C2','waitlist_accepted',701,15,'count'),('C2','waitlist_admitted',556,15,'count'),
      ('C9','sat_submit_pct',21,20,'percent'),('C9','act_submit_pct',46,20,'percent'),
      ('C9','sat_composite_p25',1290,20,'score'),('C9','sat_composite_p75',1440,20,'score'),
      ('C9','sat_ebrw_p25',620,20,'score'),('C9','sat_ebrw_p75',710,20,'score'),
      ('C9','sat_math_p25',640,20,'score'),('C9','sat_math_p75',750,20,'score'),
      ('C9','act_composite_p25',27,21,'score'),('C9','act_composite_p75',32,21,'score'),
      ('C10','hs_rank_top10_pct',67,23,'percent'),('C10','hs_rank_top25_pct',95,23,'percent'),
      ('C10','hs_rank_top50_pct',99,23,'percent'),('C10','hs_rank_reported_pct',27,23,'percent')]),
    ('Georgia Institute of Technology-Main Campus',139755,2023,
     'https://irp.gatech.edu/sites/default/files/CDS/CDS_2023-2024_V3.pdf',
     'Georgia Tech CDS main institution; C1 totals also verified against the residency breakdown on PDF p15.',
     [('C1','applicants',52377,14,'count'),('C1','admitted',8622,14,'count'),('C1','enrolled',3760,14,'count'),
      ('C2','waitlist_offered',5809,15,'count'),('C2','waitlist_accepted',4016,15,'count'),('C2','waitlist_admitted',60,15,'count'),
      ('C9','sat_submit_pct',77,20,'percent'),('C9','act_submit_pct',35,20,'percent'),
      ('C9','sat_composite_p25',1330,20,'score'),('C9','sat_composite_p75',1510,20,'score'),
      ('C9','sat_ebrw_p25',650,20,'score'),('C9','sat_ebrw_p75',740,20,'score'),
      ('C9','sat_math_p25',680,20,'score'),('C9','sat_math_p75',790,20,'score'),
      ('C9','act_composite_p25',28,20,'score'),('C9','act_composite_p75',34,20,'score')]),
    ('Georgia Institute of Technology-Main Campus',139755,2024,
     'https://irp.gatech.edu/sites/default/files/CDS/CDS_2024-2025_FINAL_20FEB2025.pdf',
     'Georgia Tech CDS main institution. C1 total checked against 2024 in-state/out-of-state/international subtotal on PDF p7.',
     [('C1','applicants',59789,7,'count'),('C1','admitted',8413,7,'count'),('C1','enrolled',3850,7,'count'),
      ('C2','waitlist_offered',6481,7,'count'),('C2','waitlist_accepted',4471,7,'count'),('C2','waitlist_admitted',201,7,'count')]),
]

def main():
    observations=[]; sources=[]
    for school,unitid,year,url,notes,values in ENTRIES:
        edition=f'{year}-{year+1}'
        binary_name = (f'uiuc_{year}.xlsx' if 'uofi.box.com' in url else
                       f'umd_{year}.xlsx' if 'irpa.umd.edu' in url else
                       f'uw_{year}.xlsx' if 'finance.uw.edu' in url and year==2023 else
                       f'uw_{year}.pdf' if 'finance.uw.edu' in url else
                       f'osu_{year}.pdf' if 'irp.osu.edu/media/276' in url else
                       f'purdue_{year}.xlsx' if 'purdue.edu' in url else
                       f'utexas_{year}.pdf' if 'utexas.' in url else
                       f'wisconsin_{year}.pdf' if 'uwmadison.app.box.com' in url else None)
        binary=HERE.parent.parent/'raw/v2b'/binary_name if binary_name else None
        if binary and not binary.is_file():raise FileNotFoundError(binary)
        local=str(binary.relative_to(HERE.parent.parent)) if binary else ''
        sha=hashlib.sha256(binary.read_bytes()).hexdigest() if binary else ''
        fmt=binary.suffix.lstrip('.') if binary else ('html' if '.php' in url else 'pdf')
        status='official_binary_table_reviewed' if binary else 'official_web_render_reviewed'
        source_notes=(notes if binary or fmt=='html' else 'Official university PDF opened as web rendered/indexed source; local TLS prevented binary download. '+notes)
        sources.append(dict(school=school,unitid=unitid,cohort_year=year,cds_edition=edition,source_url=url,
                            local_path=local,sha256=sha,retrieved_at=date.today().isoformat(),format=fmt,
                            status=status,notes=source_notes))
        for section,metric,value,page,unit in values:
            method=('derived_sum_of_reported_categories' if ((school=='University of Wisconsin-Madison' and year==2024 and section=='C1') or
                                                              (school=='Purdue University-Main Campus' and year==2024 and metric=='admitted_sum_of_reported_categories'))
                    else 'manual_official_table_transcription')
            observations.append(dict(school=school,unitid=unitid,cohort_year=year,cds_edition=edition,section=section,
                                     metric=metric,population='first_time_first_year',gender='total',residency='all',
                                     value=value,unit=unit,source_url=url,page=page,
                                     extraction_method=method,verification_status='source_table_reviewed',notes=notes))
    for filename,rows,fields in [('observations.csv',observations,OBS),('sources.csv',sources,SRC)]:
        with (HERE/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print(len(sources),'school-years',len(observations),'observations')

if __name__=='__main__':main()
