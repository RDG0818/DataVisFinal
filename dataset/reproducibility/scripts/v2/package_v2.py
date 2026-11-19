#!/usr/bin/env python3
"""Integrate accepted CDS shards and the all-ADM IPEDS backbone for private review."""
import csv
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
K=ROOT/'kaggle_v2'
HANDLE='yangkuangou/us-college-admissions-panel-ipeds-cds-2014-2024'
def read(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,cols):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
def num(s):return float(s) if s not in ('',None) else None
def main():
    K.mkdir(exist_ok=True)
    panel=read('data/ipeds_admissions_panel.csv')
    inst=read('data/institutions.csv')
    long=read('data/cds_long.csv');wide=read('data/cds_wide.csv')
    assert len({(r['unitid'],r['cohort_year']) for r in panel})==len(panel)
    assert len({r['unitid'] for r in inst})==len(inst)
    assert {r['unitid'] for r in panel}=={r['unitid'] for r in inst}
    assert {int(r['cohort_year']) for r in panel}==set(range(2014,2025))
    # Preserve every accepted v1 value and denominator. Newly reviewed values are additive.
    key=lambda r:tuple(r[k] for k in ['unitid','cohort_year','section','metric','population','gender','residency'])
    old=read('kaggle/cds_long.csv');new={key(r):r for r in long}
    assert all(key(r) in new and num(new[key(r)]['value'])==num(r['value']) for r in old)
    windex={(r['unitid'],r['cohort_year']):r for r in wide}
    for r in long:
        field=r['metric']
        if r['population']!='first_time_first_year' and r['metric']!='undergraduate_enrollment':field+='__population_'+r['population']
        if r['gender']!='total':field+='__gender_'+r['gender']
        if r['residency']!='all':field+='__residency_'+r['residency']
        wr=windex[(r['unitid'],r['cohort_year'])]
        assert num(wr[field])==num(r['value'])
        assert field in json.loads(wr['field_provenance'])
    for src,dest in [('data/cds_long.csv','data/cds_enrichment_long.csv'),('data/cds_wide.csv','data/cds_enrichment_wide.csv')]:shutil.copyfile(ROOT/src,ROOT/dest)
    cds_sources=[s for s in read('sources.csv') if s.get('source_type','university_cds')=='university_cds']
    # build_panel.py writes the CDS manifest; this script leaves it intact for repeatability.
    ids={s['source_id'] for s in cds_sources}
    assert all(r['source_id'] in ids for r in long)
    combined=[dict(s,source_type='university_cds',license_note='University source document retains its own rights; factual compilation CC BY 4.0') for s in cds_sources]
    for s in read('validation/ipeds_v2_sources.csv'):
        d=dict(s,source_type='nces_ipeds',license_note='Public domain US federal statistical data')
        d['source_url']=s.get('official_source_url') or s.get('source_url','')
        d['source_id']=s.get('source_id') or 'ipeds_'+hashlib.sha256((s.get('table','')+'|'+d['source_url']).encode()).hexdigest()[:16]
        combined.append(d)
    for s in read('validation/ipeds_v2_codebook_sources.csv'):
        d=dict(s,source_type='nces_ipeds_codebook',license_note='Public domain US federal metadata')
        d['source_url']=s.get('source_url') or s.get('url','')
        d['source_id']='nces_codebook_'+str(s.get('year',s.get('cohort_year','')))
        d['sha256']=s.get('sha256') or s.get('source_sha256','')
        combined.append(d)
    cols=['source_id','source_type','school','unitid','cohort_year','cohort_years','cds_edition','table','source_url','local_path','sha256','retrieved_at','release_status','format','status','access_method','license_note','notes']
    cols+=sorted({k for s in combined for k in s}-set(cols))
    write('kaggle_v2/sources.csv',combined,cols)
    write('sources.csv',combined,cols)
    # Explicit, reproducible CDS/IPEDS discrepancies; no reconciliation or filling.
    pi={(r['unitid'],r['cohort_year']):r for r in panel}
    comps=[]
    for r in long:
        if not (r['section']=='C1' and r['metric'] in ['applicants','admitted','enrolled'] and r['population']=='first_time_first_year' and r['gender']=='total' and r['residency']=='all'):continue
        ip=pi.get((r['unitid'],r['cohort_year']),{});iv=ip.get(r['metric'],'')
        delta='' if iv=='' else num(r['value'])-num(iv)
        ip_source=next((s['source_id'] for s in combined if s.get('table')=='ADM'+r['cohort_year']), '')
        comps.append(dict(school=r['school'],unitid=r['unitid'],cohort_year=r['cohort_year'],metric=r['metric'],cds_value=r['value'],ipeds_value=iv,cds_minus_ipeds=delta,status='not_available' if iv=='' else 'exact_match' if delta==0 else 'difference_preserved',cds_source_url=r['source_url'],cds_page=r['page'],ipeds_source_id=ip_source,notes='Different releases and reporting footprints can differ; original values preserved.'))
    write('validation/v2/consistency.csv',comps,list(comps[0]))
    source_issues=[]
    for r in long:
        if r['unitid']=='243780' and r['cohort_year']=='2024' and r['metric']=='admitted':
            source_issues.append(dict(school=r['school'],unitid=r['unitid'],cohort_year=r['cohort_year'],metric='admitted',severity='warning',issue='Official printed total 30272 versus both gender and residency sums 39272. Primary preserves 30272; separate derived metric preserves 39272. No editorial correction is imposed.',source_url=r['source_url'],page=r['page']))
        if r['unitid']=='201645' and r['cohort_year']=='2024' and r['metric']=='act_submit_pct':
            source_issues.append(dict(school=r['school'],unitid=r['unitid'],cohort_year=r['cohort_year'],metric=r['metric'],severity='warning',issue='Reported ACT share 23% differs from the accompanying 269 score submitters / C1 1619 enrolled. Reported percent retained; denominator/version cause unverified.',source_url=r['source_url'],page=r['page']))
    write('validation/v2/source_inconsistencies.csv',source_issues,['school','unitid','cohort_year','metric','severity','issue','source_url','page'])
    coverage=Counter(r['cohort_year'] for r in panel)
    cdsy=Counter(r['cohort_year'] for r in wide)
    both={r['unitid'] for r in wide if r['cohort_year']=='2023'} & {r['unitid'] for r in wide if r['cohort_year']=='2024'}
    summ=dict(ipeds_institutions=len(inst),ipeds_institution_years=len(panel),ipeds_year_coverage=dict(sorted(coverage.items())),cds_schools=len({r['unitid'] for r in long}),cds_school_years=len(wide),cds_observations=len(long),cds_year_coverage=dict(sorted(cdsy.items())),cds_schools_both_2023_2024=len(both),cds_2023_2024_schools=len({r['unitid'] for r in wide if r['cohort_year'] in ['2023','2024']}),v1_observations_preserved=len(old),cds_ipeds_status=dict(Counter(r['status'] for r in comps)),source_documents=len(combined),checks={'unique_keys':True,'all_adm_years_present':True,'institution_universe_equal':True,'v1_values_preserved':True,'long_wide_all_values_equal':True,'all_cds_source_ids_resolve':True})
    (ROOT/'validation/v2/integration_summary.json').write_text(json.dumps(summ,indent=2)+'\n')
    # Preserve the CDS metric explanations and add the IPEDS annual schema.
    schema=(ROOT/'scripts/v2_ipeds/IPEDS_SCHEMA.md').read_text()
    cdict=(ROOT/'DATA_DICTIONARY_CDS.md').read_text().replace('`cds_long.csv`','`cds_enrichment_long.csv`').replace('`cds_wide.csv`','`cds_enrichment_wide.csv`')
    dictionary='''# US College Admissions Panel 2014–2024: IPEDS + CDS

## Tables, scope and joins

| File | Grain and purpose |
|---|---|
| `ipeds_admissions_panel.csv` | Every published ADM institution × entering-fall year, 2014–2024; same-year HD attributes |
| `institutions.csv` | One UNITID, most recent available same-source directory profile; snapshot year is explicit |
| `cds_enrichment_long.csv` | Exact metric × population × category observation; official source URL and page |
| `cds_enrichment_wide.csv` | Institution × actual cohort year; all populated fields carry JSON provenance |
| `sources.csv` | All used NCES tables and university documents, URLs, available hashes and release status |
| `ipeds_variable_mapping.csv` | Original IPEDS variables to readable names, annual availability and units |
| `validation.zip` | Row coverage, field coverage, rule findings, source and difference checks |
| `reproducibility.zip` | Acquisition/build code, frozen CDS observations and source manifests |

Join on `unitid` and `cohort_year`. The backbone covers all ADM reporters, including non-four-year institutions and US jurisdictions. It is not every institution in HD and is not a balanced panel. No missing institution-year is synthesized. A blank never means zero. Current institution profiles must not be substituted for historical control, names, classifications or locations in the panel. A stable UNITID does not guarantee a stable institutional footprint; mergers and branch reorganizations require further research.

Counts are institution reports, not national unique people. Derived admission rate = admitted/applicants and yield = enrolled/admitted, with positive denominators. Preserve source missingness and NCES imputation/status flags. The 2024 release is provisional; earlier acquired releases are labeled individually. No custom imputation or interpolation is performed.

CDS enrichment retains the accepted v1 observations from 2019–2025, with this round prioritizing 2023 and 2024. Its range is deliberately wider than the IPEDS title range. The two layers are not silently combined or overwritten; `validation/v2/consistency.csv` inside the archive records exact differences. Source scope can differ (for example, Columbia College/Engineering vs the UNITID, or Purdue campus reorganizations).

## Source rights

NCES IPEDS federal statistical data are public domain. [US Department of Education copyright guidance](https://www.ed.gov/about/contact-us/faqs) and the [official IPEDS download portal](https://nces.ed.gov/ipeds/use-the-data). Original compilation, documentation and code: CC BY 4.0, attribution to yangkuangou and source institutions. University CDS documents retain their own rights; original university PDFs are not bundled or relicensed. No endorsement is implied. Source URLs in `sources.csv` and the CDS long table identify the evidence for numeric observations.

## IPEDS definitions and annual variable mapping

'''+schema+'\n\n## Explicit CDS source inconsistencies\n\nPurdue 2024 has `admitted=30272` in the official printed total CDS-C!C42, while independently summing the gender categories (22551+16721) or residency categories (9091+25935+4246) gives 39272. `admitted_sum_of_reported_categories=39272` preserves that alternative as a separate derived metric. Default CDS rates use the reported `admitted`; the alternative is not substituted. The reporting footprint expands in 2024 to West Lafayette, Indianapolis and Polytechnic Statewide. Case Western 2024 reports ACT submission of 23% beside 269 submitters, whereas C1 enrolled is 1619; preserve the reported percentage and flag the unresolved denominator/version difference. See the source inconsistency table in validation.zip.\n\n## CDS definitions (retained and renamed from v1)\n\n'+cdict
    (ROOT/'DATA_DICTIONARY.md').write_text(dictionary)
    desc=f'''How did applications, admission rates and enrollment yield change over a decade—and what do waitlists and student profiles add to that picture? This dataset connects **every published NCES IPEDS ADM report from 2014–2024** with a carefully sourced Common Data Set enrichment layer. Build national or institution-level trends from the IPEDS backbone, then drill into CDS-only detail without losing denominators, document pages or disagreements.

**{len(inst):,} institutions · {len(panel):,} observed institution-years · 11 entering-fall cohorts**  
CDS enhancement: **{summ['cds_schools']} colleges and universities · {len(wide)} school-years · {len(long):,} numeric observations**. {len(both)} institutions have both 2023 and 2024 CDS coverage. Actual field coverage is in the validation files; the CDS layer also preserves previously verified 2019–2025 observations.

### Three analysis entry points

1. **The admissions decade:** pair institutions over time; compare application growth, admission-rate changes and public/private nonprofit yield.
2. **The score-submission shift:** track SAT/ACT submission shares in a fixed reporting cohort; inspect annual policy definitions and missingness.
3. **Beyond IPEDS:** use CDS waitlists, GPA, class rank and selected need-based aid; trace each observation to the source table.

### Read it in five lines
```python
import pandas as pd
from pathlib import Path
root = next(Path('/kaggle/input').rglob('ipeds_admissions_panel.csv')).parent
panel = pd.read_csv(root / 'ipeds_admissions_panel.csv')
panel.query('cohort_year == 2024').sort_values('applicants', ascending=False).head()
```

### Files and principal fields

| Table | Key fields | Use |
|---|---|---|
| `ipeds_admissions_panel.csv` | `unitid`, `cohort_year`, `applicants`, `admitted`, `enrolled`, gender counts | Every ADM reporting institution-year, with derived admission and yield rates |
| Same IPEDS table | SAT/ACT 25th/75th scores, submission percentages, annual policy labels, NCES flags | Scores describe submitters; missing is never zero |
| Same IPEDS table / `institutions.csv` | School name, state, historical control, Carnegie classifications, coordinates | Historical HD in panel; explicitly dated latest profiles in institutions |
| `cds_enrichment_long.csv` | `metric`, `population`, `gender`, `residency`, `value`, `source_url`, `page` | Authoritative field-level CDS provenance |
| `cds_enrichment_wide.csv` | `unitid`, `cohort_year`, metric columns, `field_provenance` | Convenient exploration with exact provenance |
| `sources.csv`, `ipeds_variable_mapping.csv` | Official URLs, source hashes/release status; raw variable names | Audit and original-name lookup |
| `DATA_DICTIONARY.md`, `validation.zip`, `reproducibility.zip` | Definitions, coverage, checks, retained discrepancies, build code | Reproducible review |

### Boundaries that matter

This is an **unbalanced institutional panel** of ADM reporters, not all colleges or unique applicants. Open-admission institutions outside ADM are not added. A stable UNITID may mask changing campus scope. Use same-year HD attributes for historical comparisons, and check denominators before calculating rates. The 2024 release is provisional. SAT definitions and policy categories change during the decade; raw mappings, missing codes and NCES flags are retained. SAT and ACT submitter groups overlap. Score percentiles are conditional on submitters; composite percentiles are never synthesized by adding section percentiles. GPA scales are not automatically comparable. Aid means apply to recipients.

CDS and IPEDS can report different populations or revisions. **Both original values remain available**; no interpolation, zero filling or cross-source substitution is used. Numerical rule findings and source comparisons are preserved in `validation.zip`.

### Sources and license

IPEDS: [NCES official downloads](https://nces.ed.gov/ipeds/use-the-data), ADM and same-year HD, 2014–2024. Federal IPEDS data are **public domain**; see [Department of Education copyright guidance](https://www.ed.gov/about/contact-us/faqs). CDS: official university publications, with exact URLs and PDF pages/worksheet locations in the long table and source register. Original university documents retain their rights and are not bundled. Compilation, original code and documentation: **CC BY 4.0**. Please attribute yangkuangou and the source institutions.

A companion starter notebook provides six reproducible figures and data-derived captions. This dataset is a **private review draft**; public release is reserved for the project Leader.
'''
    (K/'README.md').write_text(desc)
    for f in ['ipeds_admissions_panel.csv','institutions.csv','cds_enrichment_long.csv','cds_enrichment_wide.csv']:shutil.copyfile(ROOT/'data'/f,K/f)
    shutil.copyfile(ROOT/'DATA_DICTIONARY.md',K/'DATA_DICTIONARY.md')
    shutil.copyfile(ROOT/'validation/ipeds_variable_mapping.csv',K/'ipeds_variable_mapping.csv')
    with zipfile.ZipFile(K/'validation.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((ROOT/'validation').rglob('*')):
            if p.is_file():z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(K/'reproducibility.zip','w',zipfile.ZIP_DEFLATED) as z:
        paths=[*list((ROOT/'scripts').rglob('*.py')),*list((ROOT/'scripts').rglob('kernel-metadata.json')),*list((ROOT/'scripts/v2_ipeds').rglob('*.md')),*list((ROOT/'shards').rglob('*.csv')),*list((ROOT/'shards').rglob('*.py')),*list((ROOT/'shards').rglob('README.md')),ROOT/'SHARD_CONTRACT.md',ROOT/'DATA_DICTIONARY_CDS.md',ROOT/'kaggle/cds_long.csv',ROOT/'kaggle/dataset-metadata.json',ROOT/'validation/ipeds_sources.csv',ROOT/'validation/ipeds_v2_policy_codes.csv',ROOT/'raw/ipeds_v2/acquisition_manifest.json']
        paths.extend(ROOT/s['local_path'] for s in read('validation/ipeds_v2_sources.csv'))
        for p in sorted(set(paths)):z.write(p,p.relative_to(ROOT))
    # Use the detailed v1 descriptions for shared provenance/metric fields.
    prev=json.loads((ROOT/'kaggle/dataset-metadata.json').read_text())
    olddesc={f['name']:f['description'] for r in prev['resources'] for f in r.get('schema',{}).get('fields',[])}
    special={'source_type':'nces_ipeds for federal tables, nces_ipeds_codebook for annual metadata, or university_cds for university reports',
      'license_note':'Rights of this underlying source; does not relicense university documents',
      'institution_name':'Institution name from the same-year HD source; institutions.csv is an explicitly dated latest profile',
      'control_label':'Same-year HD control: public, private nonprofit or private for-profit; not a current label projected backward',
      'admit_rate':'Derived admitted/applicants, 0–1, blank when denominator is nonpositive or unavailable',
      'yield_rate':'Derived enrolled/admitted, 0–1, blank when denominator is nonpositive or unavailable',
      'test_policy_label':'Year-specific NCES ADMCON7 meaning; categories change across years, see dictionary',
      'cohort_year':'Actual entering-fall year; CDS aid follows the aid academic-year start, not the PDF edition',
      'state':'Same-year two-character HD state or US jurisdiction abbreviation',
      'sat_submit_pct':'Enrolled first-years submitting SAT, percent 0–100; overlaps ACT submitters',
      'act_submit_pct':'Enrolled first-years submitting ACT, percent 0–100; overlaps SAT submitters',
      'admitted_sum_of_reported_categories':'Purdue 2024 alternative derived admission count 39272: both gender and residency sums; reported admitted remains 30272, and default rates use the reported total'}
    mapping=read('validation/ipeds_variable_mapping.csv')
    for r in mapping:
        col=r.get('readable_column') or r.get('column') or r.get('output_column') or r.get('field') or r.get('readable_name') or r.get('column_name')
        if col:
            special.setdefault(col, r.get('description') or r.get('definition') or f"{col.replace('_',' ')}; original IPEDS {r.get('component','')} variable {r.get('ipeds_variable',r.get('original_variable',''))}; unit {r.get('unit','')}; published years {r.get('years_present','')}. {r.get('notes','')}")
    filedesc={'ipeds_admissions_panel.csv':'All official ADM institution-year rows 2014–2024 with readable admissions fields and same-year HD attributes',
      'institutions.csv':'One profile for every ADM UNITID, most recent available HD year explicitly identified',
      'cds_enrichment_long.csv':'Source-preserving official CDS numeric observations with exact population and source page',
      'cds_enrichment_wide.csv':'One CDS institution-year, numeric metrics and JSON field provenance',
      'sources.csv':'All official university and NCES sources used; exact URLs, release status, available hashes and rights',
      'ipeds_variable_mapping.csv':'Readable output fields mapped to original IPEDS variables and annual semantics',
      'validation.zip':'Coverage, numeric rule findings, source evidence and CDS/IPEDS differences; original values are unchanged',
      'reproducibility.zip':'Frozen acquisition, build and packaging code plus reviewed CDS observations and source manifests',
      'README.md':'Dataset overview, five-line quickstart, analysis ideas, source links and licensing',
      'DATA_DICTIONARY.md':'Units, populations, time alignment, missing codes, original-variable mapping and caveats',
      'cover.png':'Original typographic cover for the 2014–2024 institutional admissions panel'}
    resources=[]
    for path in sorted(K.iterdir()):
        if path.name in ['dataset-metadata.json','manifest.json'] or path.is_dir():continue
        r={'path':path.name,'description':filedesc.get(path.name,path.stem.replace('_',' '))}
        if path.suffix=='.csv':
            with path.open(encoding='utf-8-sig',newline='') as f:headers=next(csv.reader(f))
            fields=[]
            for h in headers:
                description=special.get(h) or olddesc.get(h)
                if not description:
                    if 'flag' in h or h.startswith('x_'):description=f'NCES source/status flag for {h.replace("_"," ")}; blank if that flag was not published; see IPEDS mapping'
                    elif h.endswith('_code'):description=f'Original NCES categorical code for {h[:-5].replace("_"," ")}; see dictionary for annual definitions'
                    elif h.startswith('sat_') or h.startswith('act_'):description=f'{h.replace("_"," ")}; reported score among submitters, not all enrolled students; see annual definitions'
                    elif h.startswith('applicants') or h.startswith('admitted') or h.startswith('enrolled'):description=f'{h.replace("_"," ")}; reported first-time entering-fall count, matching the labeled category'
                    else:description=h.replace('_',' ').capitalize()+'; see DATA_DICTIONARY.md and ipeds_variable_mapping.csv for source and scope'
                numeric=(h in ['unitid','cohort_year','metadata_year','first_adm_year','last_adm_year','adm_year_count','value','admit_rate','yield_rate','latitude','longitude','has_matching_hd'] or h.endswith('_code') or h.startswith(('applicants','admitted','enrolled','sat_','act_','hs_','waitlist_','undergraduate_enrollment','aid_')))
                if h in ['sat_reading_definition','test_policy_era']:numeric=False
                fields.append({'name':h,'description':description,'type':'number' if numeric else 'string'})
            r['schema']={'fields':fields}
        resources.append(r)
    if not any(r['path']=='manifest.json' for r in resources):
        resources.append({'path':'manifest.json','description':'SHA-256 and byte lengths of every packaged artifact; excludes this manifest to avoid self-reference'})
    metadata={'title':'US College Admissions Panel 2014–2024: IPEDS + CDS','id':HANDLE,
      'subtitle':f'{len(inst):,} institutions, 11 cohorts, official IPEDS backbone and sourced CDS detail',
      'description':desc,'licenses':[{'name':'CC-BY-4.0'}],
      'keywords':['education','universities-and-colleges','united-states','exploratory-data-analysis'],
      'isPrivate':True,'expectedUpdateFrequency':'annually','image':'cover.png',
      'userSpecifiedSources':'NCES official IPEDS ADM and HD, entering fall 2014–2024 (federal public domain); official university Common Data Sets. Exact URLs, release status, hashes and pages in sources.csv and cds_enrichment_long.csv.',
      'resources':resources}
    assert len(metadata['title'])<=50 and len(metadata['subtitle'])<=80
    assert all(f['description'].strip() for r in resources for f in r.get('schema',{}).get('fields',[]))
    (K/'dataset-metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n')
    manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in K.iterdir() if p.is_file() and p.name!='manifest.json'}
    (K/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summ,indent=2))

if __name__=='__main__':main()
