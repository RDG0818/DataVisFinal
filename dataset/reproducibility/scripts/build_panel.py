#!/usr/bin/env python3
"""Combine independently sourced CDS observations; never impute a CDS value."""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ["applicants", "admitted", "enrolled"]
EXPECTED = CORE + ["waitlist_offered", "waitlist_accepted", "waitlist_admitted",
    "sat_submit_pct", "act_submit_pct"] + [f"{s}_p{q}" for s in
    ["sat_composite", "sat_ebrw", "sat_math", "act_composite"] for q in [25,50,75]] + [
    "hs_rank_top10_pct", "hs_rank_top25_pct", "hs_rank_top50_pct", "hs_rank_reported_pct",
    "hs_gpa_mean", "undergraduate_enrollment", "aid_need_determined_count",
    "aid_need_based_received_count", "aid_need_based_grant_received_count", "aid_need_fully_met_count", "aid_need_met_pct",
    "aid_need_based_grant_mean_usd"]

def read(p):
    with p.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write(p, rows, fields):
    p.parent.mkdir(exist_ok=True, parents=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def shortid(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def n(s): return Decimal(str(s).replace(",", "").replace("%", "").strip())

def main():
    raw=[]
    for p in sorted((ROOT/"shards").glob("*/observations.csv")):
        for r in read(p):
            r["shard"]=p.parent.name
            raw.append(r)
    if not raw: raise SystemExit("No source observations")
    keycols=["unitid","cohort_year","section","metric","population","gender","residency"]
    unique={}; conflicts=[]; exclusions=[]
    for r in raw:
        for k in ["population","gender","residency"]:
            if not r.get(k): r[k] = {"population":"first_time_first_year", "gender":"total", "residency":"all"}[k]
        r["unitid"]=str(int(r["unitid"]));r["cohort_year"]=str(int(r["cohort_year"]))
        if not 2019<=int(r["cohort_year"])<=2025:
            exclusions.append(dict(r,exclusion_reason="outside_target_years"));continue
        if not r.get("source_url", "").startswith("http") or not r.get("page"):
            exclusions.append(dict(r,exclusion_reason="missing_provenance"));continue
        if not r.get("value", "").strip(): continue
        if r.get("verification_status") not in ["source_table_reviewed"]:
            exclusions.append(dict(r,exclusion_reason="source_table_or_page_not_verified"));continue
        if "unverified" in r["page"].lower() or "search-index" in r["page"].lower():
            exclusions.append(dict(r,exclusion_reason="physical_page_not_verified"));continue
        try: val=n(r["value"])
        except Exception:
            exclusions.append(dict(r,exclusion_reason="not_numeric"));continue
        r["value"]=format(val,"f")
        r["unit"]={"gpa_points":"gpa","percentage":"percent","pct":"percent","students":"count","persons":"count"}.get(r["unit"],r["unit"])
        key=tuple(r.get(k,"") for k in keycols)
        if key in unique:
            if n(unique[key]["value"])!=val:
                conflicts.extend([dict(unique[key],exclusion_reason="conflicting_duplicate"),dict(r,exclusion_reason="conflicting_duplicate")])
            continue
        unique[key]=r
    if conflicts:
        write(ROOT/"validation/conflicting_observations.csv",conflicts,list(conflicts[0]))
        raise SystemExit("Conflicting duplicates need explicit adjudication")
    grouped=defaultdict(list)
    for r in unique.values():grouped[(r["unitid"],r["cohort_year"])].append(r)
    accepted={}
    for key,rs in grouped.items():
        totals={r["metric"]:r for r in rs if r["gender"]=="total" and r["residency"]=="all" and r["population"]=="first_time_first_year" and r["section"]=="C1"}
        if not all(k in totals for k in CORE):
            exclusions.extend(dict(r,exclusion_reason="incomplete_c1_total_triple") for r in rs);continue
        accepted[key]=rs
    rows=[r for rs in accepted.values() for r in rs]
    issues=[]
    def issue(r,rule,severity,detail): issues.append({"school":r["school"],"unitid":r["unitid"],"cohort_year":r["cohort_year"],"rule":rule,"severity":severity,"detail":detail,"source_url":r["source_url"],"page":r["page"]})
    for key,rs in accepted.items():
        bypop=defaultdict(dict)
        for r in rs:
            bypop[(r["population"],r["gender"],r["residency"])][r["metric"]]=r
            v=n(r["value"])
            if v<0:issue(r,"nonnegative","error",r["metric"])
            if r["unit"] in ["percent","percentage","pct"] and not 0<=v<=100:issue(r,"percent_range","error",r["metric"])
            if r["unit"] in ["count","students","persons"] and v!=v.to_integral_value():issue(r,"integer_count","error",r["metric"])
            if r["metric"].startswith("sat_") and re.search(r"_p(25|50|75)$",r["metric"]):
                lo,hi=(400,1600) if "composite" in r["metric"] else (200,800)
                if not lo<=v<=hi:issue(r,"sat_range","error",r["metric"])
            if r["metric"].startswith("act_") and re.search(r"_p(25|50|75)$",r["metric"]) and not 1<=v<=36:issue(r,"act_range","error",r["metric"])
            if r["metric"]=="hs_gpa_mean" and not 0<=v<=6:issue(r,"gpa_plausibility","error",r["metric"])
        for pop,d in bypop.items():
            for left,right in [("enrolled","admitted"),("admitted","applicants"),("waitlist_admitted","waitlist_accepted"),("waitlist_accepted","waitlist_offered")]:
                if left in d and right in d and n(d[left]["value"])>n(d[right]["value"]):issue(d[left],"count_order","error",f"{left}>{right}; {pop}")
            for score in ["sat_composite","sat_ebrw","sat_math","act_composite"]:
                qs=[d[f"{score}_p{q}"] for q in [25,50,75] if f"{score}_p{q}" in d]
                if any(n(a["value"])>n(b["value"]) for a,b in zip(qs,qs[1:])):issue(qs[0],"percentile_order","error",score)
            for lo,hi in [("aid_need_based_received_count","aid_need_determined_count"),("aid_need_based_grant_received_count","aid_need_based_received_count"),("aid_need_fully_met_count","aid_need_determined_count"),("hs_rank_top10_pct","hs_rank_top25_pct"),("hs_rank_top25_pct","hs_rank_top50_pct")]:
                if lo in d and hi in d and n(d[lo]["value"])>n(d[hi]["value"]):issue(d[lo],"nested_population_order","error",f"{lo}>{hi}")
        for metric in CORE:
            d={r["gender"]:r for r in rs if r["metric"]==metric and r["section"]=="C1" and r["residency"]=="all" and r["population"]=="first_time_first_year"}
            if all(g in d for g in ["total","male","female"]):
                summ=sum(n(x["value"]) for g,x in d.items() if g!="total")
                if summ!=n(d["total"]["value"]):issue(d["total"],"gender_sum","warning",f"{metric}: reported total {d['total']['value']} vs categories {summ}; extra/unknown categories may be unreported")
    sources=[];sourcemap={};sourceyears=defaultdict(set)
    for r in rows:
        sid=shortid(r["unitid"]+"|"+r["cds_edition"]+"|"+r["source_url"])
        r["source_id"]=sid
        sourceyears[sid].add(r["cohort_year"])
        sourcemap[sid]={"source_id":sid,"school":r["school"],"unitid":r["unitid"],"cohort_year":r["cohort_year"],"cds_edition":r["cds_edition"],"source_url":r["source_url"],"access_method":"see shard manifest","local_path":"","sha256":"","retrieved_at":"","format":"","notes":""}
    manifests=[]
    for p in sorted((ROOT/"shards").glob("*/sources.csv")):manifests.extend(read(p))
    for s in sourcemap.values():
        found=[m for m in manifests if m.get("source_url")==s["source_url"]]
        if found:
            for k,v in found[0].items():
                if k not in ["source_id","school","unitid","cohort_year","cds_edition","source_url"]:s[k]=v
        years=sorted(sourceyears[s["source_id"]])
        s["cohort_years"]=";".join(years)
        s["cohort_year"]=years[0] if len(years)==1 else ""
        sources.append(s)
    ipeds={}
    ipeds_paths=sorted((ROOT/"raw/ipeds").glob("ADM*.csv"))+sorted((ROOT/"raw/ipeds/remote").glob("ADM*.csv"))+sorted((ROOT/"raw/ipeds/newer_remote").glob("ADM*.csv"))
    ipeds_provenance={}
    if (ROOT/"validation/ipeds_sources.csv").exists():
        ipeds_provenance={r["local_path"]:r for r in read(ROOT/"validation/ipeds_sources.csv")}
    for p in ipeds_paths:
        year=re.search(r"ADM(20\d\d)",p.name)
        if not year:continue
        for rr in read(p):
            rr={k.upper().strip():v for k,v in rr.items()}
            uid=rr.get("UNITID","").strip()
            if uid:ipeds[(uid,year[1])]=(rr,str(p.relative_to(ROOT)))
    consistency=[];match_status={}
    for key,rs in accepted.items():
        totals={r["metric"]:r for r in rs if r["section"]=="C1" and r["gender"]=="total" and r["residency"]=="all" and r["population"]=="first_time_first_year"}
        matched=ipeds.get(key)
        statuses=[]
        for metric,ipvar in [("applicants","APPLCN"),("admitted","ADMSSN"),("enrolled","ENRLT")]:
            cds=totals[metric]; iv=""; delta="";status="not_available";file=""
            if matched:
                rr,file=matched;iv=rr.get(ipvar,"").strip()
                if iv and n(iv)>=0:
                    delta=format(n(cds["value"])-n(iv),"f");status="exact_match" if n(delta)==0 else "difference_preserved"
                else:iv="";status="ipeds_missing"
            statuses.append(status)
            ipeds_url=ipeds_provenance.get(file,{}).get("official_source_url","")
            consistency.append({"school":cds["school"],"unitid":key[0],"cohort_year":key[1],"metric":metric,"cds_value":cds["value"],"ipeds_variable":ipvar,"ipeds_value":iv,"cds_minus_ipeds":delta,"status":status,"cds_source_url":cds["source_url"],"cds_page":cds["page"],"ipeds_source_url":ipeds_url,"ipeds_retrieval_file":file,"notes":"No CDS value overwritten. IPEDS acquisition provenance in ipeds_sources.csv. Blank IPEDS URL means no table acquired for this year."})
        match_status[key]="exact_match" if all(s=="exact_match" for s in statuses) else "difference_preserved" if "difference_preserved" in statuses else "not_available"
    issuekeys={(i["unitid"],i["cohort_year"]) for i in issues if i["severity"]=="error"}
    for r in rows:
        key=(r["unitid"],r["cohort_year"])
        r["rule_validation"]="error" if key in issuekeys else "passed"
        r["ipeds_c1_check"]=match_status[key]
    cols=["school","unitid","cohort_year","cds_edition","section","metric","population","gender","residency","value","unit","source_id","source_url","page","extraction_method","verification_status","rule_validation","ipeds_c1_check","notes"]
    rows.sort(key=lambda r:(r["school"],int(r["cohort_year"]),r["section"],r["metric"],r["population"],r["gender"],r["residency"]))
    write(ROOT/"data/cds_long.csv",rows,cols)
    wide=[];wcols=set(EXPECTED);coverage=[]
    def field(r):
        s=r["metric"]
        if r["population"]!="first_time_first_year" and r["metric"]!="undergraduate_enrollment":s+="__population_"+r["population"]
        if r["gender"]!="total":s+="__gender_"+r["gender"]
        if r["residency"]!="all":s+="__residency_"+r["residency"]
        return s
    for key,rs in accepted.items():
        base={"school":rs[0]["school"],"unitid":key[0],"cohort_year":key[1],"cds_edition":";".join(sorted(set(r["cds_edition"] for r in rs))),"ipeds_c1_check":match_status[key],"rule_validation":"error" if key in issuekeys else "passed"}
        provenance={}
        for r in rs:
            f=field(r)
            if f in base:raise ValueError(f"Wide collision {key} {f}")
            base[f]=r["value"];wcols.add(f)
            provenance[f]={k:r[k] for k in ["source_id","page","extraction_method","verification_status"]}
        base["source_urls"]=json.dumps(sorted(set(r["source_url"] for r in rs)),ensure_ascii=False)
        base["field_provenance"]=json.dumps(provenance,ensure_ascii=False,separators=(",",":"))
        wide.append(base)
        coverage.append({"school":rs[0]["school"],"unitid":key[0],"cohort_year":key[1],"observations":len(rs),"sections":";".join(sorted(set(r["section"] for r in rs))),"ipeds_c1_check":match_status[key],"missing_expected_metrics":";".join(m for m in EXPECTED if not any(r["metric"]==m for r in rs))})
    wide.sort(key=lambda r:(r["school"],int(r["cohort_year"])))
    write(ROOT/"data/cds_wide.csv",wide,["school","unitid","cohort_year","cds_edition","ipeds_c1_check","rule_validation"]+sorted(wcols)+["source_urls","field_provenance"])
    scol=["source_id","school","unitid","cohort_year","cohort_years","cds_edition","source_url","local_path","sha256","retrieved_at","format","status","access_method","notes"]
    write(ROOT/"sources.csv",sorted(sources,key=lambda r:(r["school"],r["cohort_year"])),scol)
    write(ROOT/"validation/consistency.csv",consistency,list(consistency[0]) if consistency else ["school"])
    write(ROOT/"validation/issues.csv",issues,["school","unitid","cohort_year","rule","severity","detail","source_url","page"])
    write(ROOT/"validation/coverage.csv",sorted(coverage,key=lambda r:(r["school"],r["cohort_year"])),list(coverage[0]))
    write(ROOT/"validation/excluded_observations.csv",exclusions,cols+["shard","exclusion_reason"])
    metriccounts=Counter(r["metric"] for r in rows)
    write(ROOT/"validation/metric_coverage.csv",[{"metric":m,"observations":metriccounts[m],"school_years":len({(r["unitid"],r["cohort_year"]) for r in rows if r["metric"]==m}),"schools":len({r["unitid"] for r in rows if r["metric"]==m})} for m in sorted(set(EXPECTED)|set(metriccounts))],["metric","observations","school_years","schools"])
    checked_schools={r["unitid"] for r in consistency if r["status"] in ["exact_match","difference_preserved"]}
    summary={"schools":len({r["unitid"] for r in rows}),"school_years":len(wide),"observations":len(rows),"years":sorted({int(r["cohort_year"]) for r in rows}),"sources":len(sources),"schools_with_ipeds_crosscheck":len(checked_schools),"ipeds_metric_status":dict(Counter(r["status"] for r in consistency)),"rule_errors":sum(i["severity"]=="error" for i in issues),"rule_warnings":sum(i["severity"]=="warning" for i in issues),"excluded_observations":len(exclusions),"verification_status":dict(Counter(r.get("verification_status","") for r in rows)),"all_missing_values_unimputed":True}
    (ROOT/"validation/summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))
    if summary["rule_errors"]:raise SystemExit("Data rule errors require source review")

if __name__=="__main__": main()
