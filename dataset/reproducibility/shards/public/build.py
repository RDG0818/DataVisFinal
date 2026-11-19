"""Transcribed, table-reviewed official CDS public-university observations.

Each row below records an official source table and its physical PDF page or
spreadsheet cell. No IPEDS or secondary values are used here.
"""
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "shards/public"
FIELDS = "school unitid cohort_year cds_edition section metric population gender residency value unit source_url page extraction_method verification_status notes".split()
SOURCE_FIELDS = "school unitid cohort_year cds_edition source_url local_path sha256 retrieved_at format status notes".split()

obs = []
sources = []
UNITID = {
    "University of California, Berkeley": "110635",
    "University of California, Los Angeles": "110662",
    "University of California, San Diego": "110680",
    "University of California, Irvine": "110653",
    "University of California, Davis": "110644",
    "University of California, Santa Barbara": "110705",
    "University of California, Riverside": "110671",
    "University of California, Santa Cruz": "110714",
    "University of Michigan-Ann Arbor": "170976",
    "University of North Carolina at Chapel Hill": "199120",
    "University of Virginia-Main Campus": "234076",
}

def add(school, year, url, values, *, pages=None, edition=None, method="official_pdf_table_web_review", method_overrides=None, local="", notes="", extra=None):
    edition = edition or f"{year}-{str(year+1)[-2:]}"
    pages = pages or {}
    sha = hashlib.sha256((ROOT/local).read_bytes()).hexdigest() if local else ""
    sources.append(dict(school=school, unitid=UNITID[school], cohort_year=year, cds_edition=edition,
        source_url=url, local_path=local, sha256=sha,
        retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        format="xlsx" if local.endswith("xlsx") else "pdf",
        status="downloaded_and_reviewed" if local else "official_pdf_web_render_table_reviewed",
        notes=notes or ("Raw PDF download unavailable from local TLS; reviewed official PDF in web renderer" if not local else "")))
    for metric, value in values.items():
        page = pages.get(metric, pages.get("default", ""))
        sect = "C2" if metric.startswith("waitlist_") else "B1" if metric == "undergraduate_enrollment" else "C9" if metric.startswith(("sat_", "act_")) else "C10" if metric.startswith("hs_rank_") else "C11" if metric.startswith("hs_gpa_") and metric != "hs_gpa_mean" else "C12" if metric == "hs_gpa_mean" else "H2" if metric.startswith("aid_") else "C1"
        obs.append(dict(school=school, unitid=UNITID[school], cohort_year=year, cds_edition=edition,
            section=sect, metric=metric, population="all_undergraduate" if sect=="B1" else "full_time_first_year" if sect=="H2" else "first_time_first_year",
            gender="total", residency="all", value=value,
            unit="percent" if metric.endswith("_pct") else "usd" if metric.endswith("_usd") else "count" if metric not in ("hs_gpa_mean",) and not metric.startswith(("sat_composite", "sat_ebrw", "sat_math", "act_composite")) else "score",
            source_url=url, page=page, extraction_method=(method_overrides or {}).get(metric,method),
            verification_status="source_table_reviewed", notes=notes))
    for row in (extra or []):
        metric,value,gender,residency,page = row
        obs.append(dict(school=school, unitid=UNITID[school], cohort_year=year, cds_edition=edition,
            section="C1",metric=metric,population="first_time_first_year",gender=gender,residency=residency,
            value=value,unit="count",source_url=url,page=page,extraction_method=method,
            verification_status="source_table_reviewed",notes=notes))

berkeley = "University of California, Berkeley"
base = "https://docs.google.com/spreadsheets/d/"
add(berkeley,2022,base+"1RcUrZcvOTKrPHttOE6JTjcqxw5oBB8tgExWX9vai5_o/edit?usp=sharing",
    dict(applicants=128226,admitted=14614,enrolled=6726,undergraduate_enrollment=32831),
    pages=dict(applicants="CDS-C!E27",admitted="CDS-C!E28",enrolled="CDS-C!E29",undergraduate_enrollment="B. enrollment and persistence!C17:H17"),
    method="official_xlsx_xml",local="raw/public/ucberkeley_2022.xlsx",
    notes="B1 total undergraduate enrollment sums full-time and part-time across reported gender categories")
add(berkeley,2023,base+"1Fl4jbuAWHzH2g2qOSCa8eASDs5PjIShNsA_-2jQwG5Q/edit?usp=sharing",
    dict(applicants=125916,admitted=14769,enrolled=6641,undergraduate_enrollment=33405),
    pages=dict(applicants="CDS-C!F20",admitted="CDS-C!F21",enrolled="CDS-C!F22",undergraduate_enrollment="CDS-B!E19"),
    method="official_xlsx_xml",local="raw/public/ucberkeley_2023.xlsx",
    notes="Official residency TOTAL; gender category subtotals do not equal this total")
add(berkeley,2024,base+"11BnFbit7JcrmFMi9iV_TMkzhUyCQ_dQHS0V8weuOHPM/edit?usp=sharing",
    dict(applicants=124245,admitted=13714,enrolled=6272,undergraduate_enrollment=33469),
    pages=dict(applicants="CDS-C!C49",admitted="CDS-C!C50",enrolled="CDS-C!C51",undergraduate_enrollment="CDS-B!C78:C81"),
    method="official_xlsx_xml",local="raw/public/ucberkeley_2024.xlsx",
    notes="B1 total undergraduate enrollment sums reported men 14293, women 18136, another gender 675, unknown 365")
add(berkeley,2025,base+"1INsGFH6MhaO-MFMBZ1Dngcn84FeN-hc0BLS0-v8TL_k/edit?gid=2118947953",
    dict(applicants=126864,admitted=14524,enrolled=6687,waitlist_offered=9102,waitlist_accepted=6479,waitlist_admitted=0,
         undergraduate_enrollment=33513),
    pages=dict(applicants="CDS-C!I37",admitted="CDS-C!I38",enrolled="CDS-C!I39",waitlist_offered="CDS-C!E52",waitlist_accepted="CDS-C!E53",waitlist_admitted="CDS-C!E54",undergraduate_enrollment="CDS-B!C29:E29"),
    method="official_xlsx_xml",local="raw/public/ucberkeley_2025.xlsx",notes="Waitlist admitted cell notes updated May 2026")

ucla="University of California, Los Angeles"
add(ucla,2022,"https://apb.ucla.edu/file/c4517b9b-1554-4daa-9194-dbc445d269e3",
    dict(applicants=149815,admitted=12844,enrolled=6462,waitlist_offered=16979,waitlist_accepted=11169,waitlist_admitted=367),
    pages=dict(default="8",waitlist_offered="9",waitlist_accepted="9",waitlist_admitted="9"))
add(ucla,2023,"https://apb.ucla.edu/file/b099e788-a3fc-4395-8842-29db4ff42da3",
    dict(applicants=145910,admitted=12737,enrolled=6585,undergraduate_enrollment=33040),
    pages=dict(applicants="15",admitted="15",enrolled="16",undergraduate_enrollment="6"),method="derived_sum_of_reported_categories",
    method_overrides={"undergraduate_enrollment":"official_pdf_table_web_review"},
    notes="C1 gender categories: applicants 64324+75500+6086; admitted 4771+7570+396; enrolled 2346+4195+44; no reported total in gender table")

ucsd="University of California, San Diego"
add(ucsd,2023,"https://ir.ucsd.edu/stats/undergrad/CDS_UCSD_2023_20242.pdf",
    dict(applicants=130845,admitted=32403,enrolled=7007),pages=dict(default="16"))
add(ucsd,2024,"https://ir.ucsd.edu/stats/undergrad/CDS_2024-2025_Final3.pdf",
    dict(applicants=134455,admitted=35989,enrolled=7330,waitlist_offered=27521,waitlist_accepted=19156,waitlist_admitted=4539),pages=dict(default="8"))
add(ucsd,2025,"https://ir.ucsd.edu/stats/undergrad/CDS-2025-2026-Final2.pdf",
    dict(applicants=136750,admitted=39054,enrolled=7801,waitlist_offered=36709,waitlist_accepted=25411,waitlist_admitted=5284),pages=dict(default="7"))

uci="University of California, Irvine"
add(uci,2020,"https://irap.uci.edu/files/2024/02/CDS2020_21-733fd668330c7e47.pdf",
    dict(applicants=97942,admitted=29301,enrolled=5765,waitlist_offered=18621,waitlist_accepted=11081,waitlist_admitted=2664),
    pages=dict(default="7"),method="derived_sum_of_reported_categories",
    notes="C1 men+women applicants 45055+52887, admitted 13362+15939, enrolled male FT2614+PT15 and female FT3128+PT8; gender categories only. C2 direct table values")
add(uci,2022,"https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/2/5478/files/2024/02/CDS2022_23-d0b1720a6b74681c.pdf",
    dict(applicants=119199,admitted=25358,enrolled=5794,undergraduate_enrollment=28661),pages=dict(default="7",undergraduate_enrollment="3"),
    method="derived_sum_of_reported_categories",local="raw/public/uci_2022.pdf",
    notes="C1 male+female only: 54710+64489 applicants; 9981+15377 admitted; 2234+2+3550+8 enrolled. C2 waitlist cells blank; no zero imputation")
add(uci,2024,"https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/2/5478/files/2025/09/CDS-2024-25.pdf",
    dict(applicants=122706,admitted=35317,enrolled=6736,waitlist_offered=13155,waitlist_accepted=6259,waitlist_admitted=6259,
         undergraduate_enrollment=30204,aid_need_determined_count=3296,aid_need_based_received_count=3229,
         aid_need_fully_met_count=826,aid_need_met_pct=85.5,aid_need_based_grant_mean_usd=25236),
    pages=dict(default="7",undergraduate_enrollment="3",aid_need_determined_count="20",aid_need_based_received_count="20",
               aid_need_fully_met_count="20",aid_need_met_pct="20",aid_need_based_grant_mean_usd="20"),
    method="official_pdf_pdftotext_table_review",local="raw/public/uci_2024.pdf",
    notes="C1 official residency TOTAL; admitted 35,317 retained as printed. H2 uses 2024-25 estimated first-time full-time aid cohort; received=H2 line D; mean grant=H2 line K")

ucd="University of California, Davis"
add(ucd,2025,"https://aggiedata.ucdavis.edu/sites/g/files/dgvnsk1841/files/media/documents/CDS_UCD_0.pdf",
    dict(applicants=102988,admitted=45674,enrolled=6824,waitlist_offered=17582,waitlist_accepted=9747,waitlist_admitted=3758,
         undergraduate_enrollment=31695),pages=dict(default="9",undergraduate_enrollment="4"),
    notes="B1 all undergraduates=12516 male+17835 female+1344 unknown")
add(ucd,2023,"https://aggiedata.ucdavis.edu/sites/g/files/dgvnsk1841/files/media/documents/CDS_2023_2024_UCD.pdf",
    dict(applicants=94627,admitted=39399,enrolled=6581,waitlist_offered=19446,waitlist_accepted=10898,waitlist_admitted=4387,
         undergraduate_enrollment=31797),pages=dict(default="12",undergraduate_enrollment="4"),
    notes="Official CDS 2023-24 C1 residency TOTAL and B1 total; section C9 test fields blank")

ucsb="University of California, Santa Barbara"
add(ucsb,2023,"https://drive.google.com/file/d/1ehjlUgc7vxtgmqtTNS8KWUN3iMfM7YyJ/view?usp=sharing",
    dict(applicants=110876,admitted=30805,enrolled=5043,waitlist_offered=15689,waitlist_accepted=9670,waitlist_admitted=5493,
         undergraduate_enrollment=23232),pages=dict(default="8",undergraduate_enrollment="3"),
    method="official_pdf_pdftotext_table_review",local="raw/public/ucsb_2023.pdf",
    notes="Original UCSB-authored CDS PDF hosted in Google Drive; file A0 identifies campus IR office and official bap.ucsb.edu CDS page; historical Drive link no longer shown on current landing page")
add(ucsb,2025,"https://drive.google.com/file/d/1FIkvY5dANho45ioG7-JHgO3IPH6-ui1W/view?usp=sharing",
    dict(applicants=110187,admitted=42093,enrolled=5081,waitlist_offered=25713,waitlist_accepted=18022,waitlist_admitted=9603,
         undergraduate_enrollment=23091,hs_gpa_4plus_pct=87.81,hs_gpa_mean=4.29,
         aid_need_determined_count=2340,aid_need_based_received_count=2282,aid_need_fully_met_count=422,
         aid_need_met_pct=82.4,aid_need_based_grant_mean_usd=32900),
    pages=dict(default="6",undergraduate_enrollment="3",hs_gpa_4plus_pct="10",hs_gpa_mean="10",
      aid_need_determined_count="20",aid_need_based_received_count="20",aid_need_fully_met_count="20",aid_need_met_pct="20",aid_need_based_grant_mean_usd="20"),
    method="official_pdf_pdftotext_table_review",local="raw/public/ucsb_2025.pdf",
    notes="Official UCSB page links this Drive PDF; H2 is 2025-26 estimated aid, received=count on H2 line D among those with determined need, mean grant=H2 line K. B1 total=9647 male+13227 female+217 unknown; GPA 4.29 as printed, weighted scale not specified")

ucsc="University of California, Santa Cruz"
add(ucsc,2023,"https://mediafiles.ucsc.edu/iraps/common-data-set/common-data-set-2023-24.pdf",
    dict(applicants=68750,admitted=42130,enrolled=4379,waitlist_offered=18398,waitlist_accepted=12285,waitlist_admitted=10812),
    pages=dict(default="6"),notes="C1 residency TOTAL and gender categories; direct UCSC-hosted PDF. C2 table values in printed order")

ucr="University of California, Riverside"
add(ucr,2023,"https://ir.ucr.edu/sites/default/files/2024-03/cds-2023-2024.pdf",
    dict(applicants=56883,admitted=40032,enrolled=5525,waitlist_offered=8074,waitlist_accepted=3891,waitlist_admitted=1145),
    pages=dict(default="9",waitlist_offered="10",waitlist_accepted="10",waitlist_admitted="10"))
add(ucr,2024,"https://ir.ucr.edu/sites/default/files/2025-04/cds-2024-2025.pdf",
    dict(applicants=57714,admitted=44356,enrolled=5419),pages=dict(default="9"))
add(ucr,2025,"https://ir.ucr.edu/sites/default/files/2026-05/cds-2025-2026.pdf",
    dict(applicants=61184,admitted=52676,enrolled=6686,waitlist_offered=3783,waitlist_accepted=2019,waitlist_admitted=0),
    pages=dict(default="9",waitlist_offered="10",waitlist_accepted="10",waitlist_admitted="10"))

umich="University of Michigan-Ann Arbor"
add(umich,2023,"https://obp.umich.edu/wp-content/uploads/pubdata/cds/CDS_2023-24_UMAA_10-25-24.pdf",
    dict(applicants=87632,admitted=15722,enrolled=7466,undergraduate_enrollment=33730),
    pages=dict(default="4",undergraduate_enrollment="2"))
add(umich,2024,"https://obp.umich.edu/wp-content/uploads/pubdata/cds/CDS_2024-25_UMAA.pdf",
    dict(applicants=98310,admitted=15373,enrolled=7278,waitlist_offered=24804,waitlist_accepted=18793),pages=dict(default="6"))
add(umich,2025,"https://obp.umich.edu/wp-content/uploads/pubdata/cds/cds_2025-26_umaa.pdf",
    dict(applicants=109112,admitted=17915,enrolled=8178,undergraduate_enrollment=35358,
        sat_submit_pct=55,act_submit_pct=18,sat_composite_p25=1370,sat_composite_p50=1470,sat_composite_p75=1530,
        sat_ebrw_p25=690,sat_ebrw_p50=730,sat_ebrw_p75=750,sat_math_p25=680,sat_math_p50=740,sat_math_p75=780,
        act_composite_p25=32,act_composite_p50=33,act_composite_p75=34),
    pages=dict(default="14",undergraduate_enrollment="3",sat_submit_pct="21",act_submit_pct="21",
      sat_composite_p25="21",sat_composite_p50="21",sat_composite_p75="21",sat_ebrw_p25="21",sat_ebrw_p50="21",sat_ebrw_p75="21",sat_math_p25="21",sat_math_p50="21",sat_math_p75="21",act_composite_p25="21",act_composite_p50="21",act_composite_p75="21"))

unc="University of North Carolina at Chapel Hill"
add(unc,2022,"https://oira.unc.edu/wp-content/uploads/sites/297/2024/02/CDS_2022-23_20240206.pdf",
    dict(applicants=57221,admitted=9640,enrolled=4435,waitlist_offered=7258,waitlist_accepted=5392,waitlist_admitted=383),pages=dict(default="7"),
    notes="C1 total enrollment 4425 full time + 10 part time = 4435; official total printed")
add(unc,2023,"https://oira.unc.edu/wp-content/uploads/sites/297/2024/07/CDS_PUBLISHED_2023_2024_07162024.pdf",
    dict(applicants=57902,admitted=10852,enrolled=4699,waitlist_offered=6154,waitlist_accepted=4633,waitlist_admitted=36,
         undergraduate_enrollment=20880,sat_submit_pct=29,act_submit_pct=34,
         sat_composite_p25=1380,sat_composite_p50=1460,sat_composite_p75=1520,
         sat_ebrw_p25=680,sat_ebrw_p50=720,sat_ebrw_p75=750,
         sat_math_p25=690,sat_math_p50=750,sat_math_p75=780,
         act_composite_p25=30,act_composite_p50=32,act_composite_p75=34,
         hs_rank_top10_pct=74.9,hs_rank_top25_pct=95.8,hs_rank_top50_pct=99.7,hs_rank_reported_pct=65.0,hs_gpa_mean=4.5,
         aid_need_determined_count=1687,aid_need_based_received_count=1687,aid_need_fully_met_count=1205,
         aid_need_met_pct=100,aid_need_based_grant_mean_usd=15344),
    pages=dict(default="12",undergraduate_enrollment="5",waitlist_offered="13",waitlist_accepted="13",waitlist_admitted="13",
        sat_submit_pct="17",act_submit_pct="17",sat_composite_p25="17",sat_composite_p50="17",sat_composite_p75="17",
        sat_ebrw_p25="17",sat_ebrw_p50="17",sat_ebrw_p75="17",sat_math_p25="17",sat_math_p50="17",sat_math_p75="17",
        act_composite_p25="17",act_composite_p50="17",act_composite_p75="17",hs_rank_top10_pct="19",hs_rank_top25_pct="19",hs_rank_top50_pct="19",hs_rank_reported_pct="19",hs_gpa_mean="20",
        aid_need_determined_count="39",aid_need_based_received_count="39",aid_need_fully_met_count="40",aid_need_met_pct="40",aid_need_based_grant_mean_usd="40"),
    notes="C12 GPA 4.5 as printed (weighted). H2 reports 2022-23 final aid cohort, one year earlier than C1; received=H2 line D, mean grant=H2 line K; need met 100% reported as policy/practice")
add(unc,2024,"https://oira.unc.edu/wp-content/uploads/sites/297/2025/08/CDS_UNCCH_2024-25_20250829.pdf",
    dict(applicants=66535,admitted=10209,enrolled=4632),pages=dict(default="9"))

uva="University of Virginia-Main Campus"
add(uva,2023,"https://ira.virginia.edu/sites/g/files/jsddwu1106/files/2023-2024-V3.1%20CDS_FINAL_508.pdf",
    dict(applicants=56528,admitted=9533,enrolled=3966,waitlist_offered=8899,waitlist_accepted=5114,waitlist_admitted=320),
    pages=dict(default="11",waitlist_offered="12",waitlist_accepted="12",waitlist_admitted="12"))
add(uva,2024,"https://ira.virginia.edu/sites/g/files/jsddwu1106/files/2025-03/CDS_2024-2025_508.pdf",
    dict(applicants=58951,admitted=9909,enrolled=3961,waitlist_offered=10470,waitlist_accepted=6759,waitlist_admitted=242,
         undergraduate_enrollment=17901,
         sat_submit_pct=45.6,act_submit_pct=13.8,sat_composite_p25=1410,sat_composite_p50=1470,sat_composite_p75=1520,
         sat_ebrw_p25=700,sat_ebrw_p50=730,sat_ebrw_p75=760,sat_math_p25=710,sat_math_p50=750,sat_math_p75=780,
         act_composite_p25=32,act_composite_p50=33,act_composite_p75=35),
    pages=dict(default="10",undergraduate_enrollment="3",waitlist_offered="11",waitlist_accepted="11",waitlist_admitted="11",
      sat_submit_pct="15",act_submit_pct="15",sat_composite_p25="15",sat_composite_p50="15",sat_composite_p75="15",
      sat_ebrw_p25="15",sat_ebrw_p50="15",sat_ebrw_p75="15",sat_math_p25="15",sat_math_p50="15",sat_math_p75="15",
      act_composite_p25="15",act_composite_p50="15",act_composite_p75="15"))

for row in obs:
    if row["school"] == unc and row["section"] == "H2" and row["cohort_year"] == 2023:
        row["cohort_year"] = 2022  # H1 explicitly selects final AY 2022-23.
    if row["metric"] == "hs_gpa_mean": row["unit"] = "gpa_points"
    if row["metric"].startswith(("sat_composite", "sat_ebrw", "sat_math", "act_composite")):
        row["unit"]="score"

OUT.mkdir(parents=True,exist_ok=True)
for name, fields, rows in (("observations.csv",FIELDS,obs),("sources.csv",SOURCE_FIELDS,sources)):
    with (OUT/name).open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
print(f"{len(obs)} observations, {len(sources)} sources, {len(set(x['school'] for x in obs))} schools")
