#!/usr/bin/env python3
"""Build the private, CPU-only starter notebook without local data science deps."""
import ast
import json
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'notebook_v2'
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip()))
def code(s):
    ast.parse(s)
    cells.append(nbf.v4.new_code_cell(s.strip()))

md('''# A decade of US college admissions
### IPEDS 2014–2024, with a source-preserving Common Data Set layer

The three data-derived takeaways below are followed by six reproducible figures.
Every comparison names its population; the accompanying dataset retains the original sources, missingness and disagreements.
This is a descriptive institutional panel, not an applicant-level prediction model. Narrative is a draft for editorial review.''')
code('''
from pathlib import Path
import base64, html, json, textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter
from IPython.display import display, Markdown

matches = sorted(Path('/kaggle/input').rglob('ipeds_admissions_panel.csv'))
assert len(matches) == 1, f'Expected one attached panel, got {matches}'
DATA = matches[0].parent
p = pd.read_csv(matches[0], low_memory=False)
cds = pd.read_csv(DATA / 'cds_enrichment_long.csv', low_memory=False)
assert not p.duplicated(['unitid','cohort_year']).any()
assert set(p.cohort_year) == set(range(2014, 2025))
for c in ['applicants','admitted','enrolled','sat_submit_pct','act_submit_pct']:
    p[c] = pd.to_numeric(p[c], errors='coerce')
p['admission_rate_pct'] = (100*p.admitted/p.applicants).where(p.applicants>0)
p['yield_pct'] = (100*p.enrolled/p.admitted).where(p.admitted>0)
OUT = Path('/kaggle/working'); OUT.mkdir(exist_ok=True)
FIG = OUT/'figures'; FIG.mkdir(exist_ok=True)
NAVY, TEAL, CORAL, GOLD = '#183247', '#087f8c', '#e4755c', '#bd8d35'
plt.rcParams.update({'figure.facecolor':'#faf9f5','axes.facecolor':'#faf9f5',
    'text.color':NAVY,'axes.labelcolor':NAVY,'xtick.color':NAVY,'ytick.color':NAVY,
    'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
    'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#bac2c5',
    'grid.color':'#dce1e1','grid.linewidth':.65,'axes.titleweight':'bold',
    'savefig.facecolor':'#faf9f5','svg.fonttype':'none'})
charts=[]; facts={}
def finish(fig, slug, title, caption, footnote, table):
    fig.suptitle(title, x=.08, y=.97, ha='left', fontsize=19, weight='bold')
    fig.text(.08,.025,footnote,fontsize=8.8,color='#546874',va='bottom')
    fig.subplots_adjust(left=.11,right=.95,top=.84,bottom=.15)
    fig.savefig(FIG/f'{slug}.png',dpi=180)
    fig.savefig(FIG/f'{slug}.svg')
    table.to_csv(OUT/f'{slug}_data.csv',index=False)
    plt.show(); plt.close(fig)
    display(Markdown('**Takeaway.** '+caption))
    charts.append(dict(slug=slug,title=title,caption=caption,footnote=footnote))

# Fixed endpoint comparison; all intervening years must have an observed rate.
eligible=p[(p.applicants>=1000)&p.admission_rate_pct.between(0,100)].copy()
balanced_ids=eligible.groupby('unitid').cohort_year.nunique().loc[lambda x:x==11].index
ep=eligible[eligible.unitid.isin(balanced_ids)].pivot(index='unitid',columns='cohort_year',values='admission_rate_pct')
latest=p[p.cohort_year.eq(2024)].set_index('unitid')
ep['change_pp']=ep[2024]-ep[2014]
test=p[p.cohort_year.between(2019,2024)&p.sat_submit_pct.between(0,100)&p.act_submit_pct.between(0,100)].copy()
test_ids=test.groupby('unitid').cohort_year.nunique().loc[lambda x:x==6].index
test=test[test.unitid.isin(test_ids)]
test_med=test.groupby('cohort_year')[['sat_submit_pct','act_submit_pct']].median()
facts.update(institutions=int(p.unitid.nunique()),institution_years=len(p),balanced_endpoint_n=len(ep),
    median_admission_rate_change_pp=float(ep.change_pp.median()),test_balanced_n=len(test_ids),
    sat_median_change_2019_2024=float(test_med.loc[2024,'sat_submit_pct']-test_med.loc[2019,'sat_submit_pct']))
display(Markdown(f"1. **{facts['institutions']:,} institutions and {len(p):,} observed institution-years** span 2014–2024; coverage changes by year.\\n"
 f"2. Among **{len(ep):,} institutions with ≥1,000 applicants and a valid rate in all 11 years**, the median 2014→2024 rate change was **{ep.change_pp.median():+.1f} percentage points**.\\n"
 f"3. Across **{len(test_ids):,} institutions reporting both tests every year in 2019–2024**, the median SAT submission share changed by **{facts['sat_median_change_2019_2024']:+.1f} points**; this is descriptive, not a policy effect."))
''')
md('''## 1 · Start with the denominator
The backbone includes every published ADM institution row, including schools outside the familiar four-year university set and US jurisdictions. Open-admission institutions outside ADM are not silently added. Changes in coverage are not changes in the number of US colleges.''')
code('''
coverage=p.groupby('cohort_year').agg(institutions=('unitid','nunique'),valid_applicants=('applicants','count'),valid_admission_rates=('admission_rate_pct','count')).reset_index()
full=int(p.groupby('unitid').cohort_year.nunique().eq(11).sum())
fig,ax=plt.subplots(figsize=(11,5.8))
ax.bar(coverage.cohort_year,coverage.institutions,color=TEAL,width=.65)
for r in coverage.itertuples(): ax.text(r.cohort_year,r.institutions+22,f'{r.institutions:,}',ha='center',fontsize=9)
ax.set(xticks=list(range(2014,2025)),ylabel='Institutions with an ADM row',ylim=(0,coverage.institutions.max()*1.16))
ax.grid(axis='y');ax.set_axisbelow(True)
caption=f'{full:,} institutions appear in all 11 years; annual ADM coverage ranges from {coverage.institutions.min():,} to {coverage.institutions.max():,} institutions.'
finish(fig,'01_coverage','Eleven years, with a visible reporting universe',caption,
 'Source: NCES IPEDS ADM. Counts are report rows, not all US institutions. Cohort year means entering fall.',coverage)
''')
md('''## 2 · Where did reported admission rates fall most?
Compare the same UNITIDs at both endpoints, requiring at least 1,000 applicants and a valid rate in every year. These are observed rate changes, not a ranking of educational quality. A stable identifier cannot guarantee an unchanged campus footprint.''')
code('''
rank=ep.nsmallest(12,'change_pp').copy()
rank['institution_name']=latest.loc[rank.index,'institution_name']
rank=rank.sort_values('change_pp',ascending=False)
fig,ax=plt.subplots(figsize=(12,8.2));y=np.arange(len(rank))
ax.hlines(y,rank[2024],rank[2014],color='#c5d0d1',linewidth=4)
ax.scatter(rank[2014],y,s=60,color='#9aaeb8',label='2014',zorder=3)
ax.scatter(rank[2024],y,s=65,color=CORAL,label='2024',zorder=3)
ax.set_yticks(y,labels=[textwrap.fill(x,34) for x in rank.institution_name]);ax.tick_params(axis='y',length=0,pad=10)
ax.set(xlabel='Applicants offered admission (%)',xlim=(0,103));ax.grid(axis='x')
ax.legend(frameon=False,ncol=2,loc='lower right')
fig.subplots_adjust(left=.40)
for i,(_,r) in enumerate(rank.iterrows()): ax.annotate(f"{r.change_pp:.1f} pp",(max(r[2014],r[2024])+1.5,i),fontsize=8,va='center')
caption=f"{rank.iloc[-1].institution_name} records the largest endpoint decline in this filtered panel ({rank.iloc[-1].change_pp:.1f} points); changing application pools and reporting scopes may contribute."
finish(fig,'02_rate_changes','The largest admission-rate declines in a fixed panel',caption,
 f'Source: NCES ADM. 12 largest declines among n={len(ep):,}; ≥1,000 applicants and a valid rate in each year.',rank.reset_index().rename(columns={2014:'rate_2014_pct',2024:'rate_2024_pct'}))
''')
md('''## 3 · The score-submitter population changed
Use a fixed cohort reporting both SAT and ACT shares in every year from 2019 through 2024. SAT and ACT groups overlap, so their percentages must not be added. Institutions that stopped reporting a score share are excluded; this creates selection and does not measure the national policy effect.''')
code('''
fig,ax=plt.subplots(figsize=(11,6));rows=[]
for field,color,label in [('sat_submit_pct',TEAL,'SAT'),('act_submit_pct',CORAL,'ACT')]:
    s=test.groupby('cohort_year')[field].agg(median='median',q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75))
    ax.plot(s.index,s['median'],marker='o',lw=2.8,color=color,label=label)
    ax.fill_between(s.index,s.q25,s.q75,color=color,alpha=.10)
    ax.text(2024.1,s.loc[2024,'median'],f"{label} {s.loc[2024,'median']:.0f}%",color=color,va='center',weight='bold')
    rows.append(s.reset_index().assign(test=label,n=len(test_ids)))
ax.axvline(2020,color=NAVY,ls=':',alpha=.6);ax.text(2020.08,96,'2020 cohort',fontsize=9)
ax.set(xlim=(2018.8,2024.9),ylim=(0,100),xticks=range(2019,2025),ylabel='Share of enrolled first-years submitting a test (%)')
ax.grid(axis='y');ax.legend(frameon=False,ncol=2,loc='upper right')
caption=f"In a fixed n={len(test_ids):,} reporting cohort, median SAT submission changed from {test_med.loc[2019,'sat_submit_pct']:.0f}% to {test_med.loc[2024,'sat_submit_pct']:.0f}%; shading shows institution-level interquartile ranges."
finish(fig,'03_test_submission','Test submission within a fixed reporting cohort',caption,
 'Source: NCES ADM. Both tests observed in all six years. Institution medians; shading = 25th–75th percentile.',pd.concat(rows))
''')
md('''## 4 · More applications, lower admission rates?
Application totals count applications to each institution, not unique people nationally. The x-axis uses log₂ growth: +1 means twice as many applications. The association is descriptive and does not show that application growth caused an admission-rate change.''')
code('''
apps=p[p.unitid.isin(ep.index)].pivot(index='unitid',columns='cohort_year',values='applicants')
growth=ep[['change_pp']].join(latest[['institution_name','control_label']])
growth['application_growth_log2']=np.log2(apps[2024]/apps[2014]);growth['applicants_2024']=apps[2024]
fig,ax=plt.subplots(figsize=(11,6.8))
for pattern,color,label in [('public',TEAL,'Public'),('private nonprofit',CORAL,'Private nonprofit'),('private for-profit',GOLD,'Private for-profit')]:
    # Labels from the package are normalized below; nonprofit never falls into for-profit.
    lower=growth.control_label.fillna('').str.lower().str.replace('_',' ')
    mask=(lower.eq('public') if pattern=='public' else lower.str.contains('private') & lower.str.contains('nonprofit|not.for.profit') if pattern=='private nonprofit' else lower.str.contains('for.profit') & ~lower.str.contains('nonprofit|not.for.profit'))
    q=growth[mask];ax.scatter(q.application_growth_log2,q.change_pp,s=18,alpha=.5,color=color,label=f'{label} (n={len(q):,})',edgecolor='none')
ax.axhline(0,lw=.8,color=NAVY,alpha=.4);ax.axvline(0,lw=.8,color=NAVY,alpha=.4)
ax.set(xlabel='Application growth, log₂(2024 / 2014)',ylabel='Admission-rate change, 2024 − 2014 (percentage points)')
ax.legend(frameon=False,fontsize=9,loc='lower left');ax.grid(alpha=.5);ax.set_axisbelow(True)
rho=growth[['application_growth_log2','change_pp']].corr(method='spearman').iloc[0,1]
caption=f'Across {len(growth):,} continuously observed institutions, application growth and admission-rate change have a Spearman correlation of {rho:.2f}; no causal interpretation is implied.'
finish(fig,'04_application_growth','Application growth vs admission-rate change',caption,
 f'Source: NCES ADM + HD. Same n={len(ep):,} endpoint cohort as Figure 2. Each point is one institution.',growth.reset_index())
facts['growth_rate_change_spearman']=float(rho)
''')
md('''## 5 · Yield by control type
Yield means enrolled ÷ admitted. Each school gets equal weight; this is the median institutional yield, not a pooled national enrollment rate. Require complete counts and stable public/private nonprofit control labels across all 11 years.''')
code('''
q=p[p.yield_pct.between(0,100)&(p.admitted>0)].copy()
q['control_group']=q.control_label.fillna('').str.lower().str.replace('_',' ')
q['control_group']=q.control_group.map(lambda s:'Public' if s=='public' else 'Private nonprofit' if ('private' in s and ('nonprofit' in s or 'not-for-profit' in s or 'not for profit' in s)) else None)
checks=q.groupby('unitid').agg(years=('cohort_year','nunique'),controls=('control_group',lambda x:x.nunique(dropna=False)))
ids=checks[(checks.years==11)&(checks.controls==1)].index
q=q[q.unitid.isin(ids)&q.control_group.notna()]
fig,ax=plt.subplots(figsize=(11,6));summaries=[]
for group,color in [('Public',TEAL),('Private nonprofit',CORAL)]:
    g=q[q.control_group.eq(group)];s=g.groupby('cohort_year').yield_pct.agg(median='median',q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75))
    assert len(s)==11, f'Unexpected control labels: {p.control_label.unique()}'
    ax.plot(s.index,s['median'],lw=2.8,marker='o',ms=4,color=color,label=f'{group} (n={g.unitid.nunique():,})')
    ax.fill_between(s.index,s.q25,s.q75,color=color,alpha=.09)
    summaries.append(s.reset_index().assign(control=group,n=g.unitid.nunique()))
ys=pd.concat(summaries)
ax.set(xticks=list(range(2014,2025)),ylim=(0,100),ylabel='Median institutional yield (%)');ax.grid(axis='y');ax.legend(frameon=False)
ends=ys[ys.cohort_year.eq(2024)].set_index('control')['median']
caption=f"In the stable reporting panel, 2024 median yield is {ends['Public']:.1f}% for public institutions and {ends['Private nonprofit']:.1f}% for private nonprofits; bands show cross-institution dispersion."
finish(fig,'05_yield_by_control','Yield trends differ across institutional control groups',caption,
 'Source: NCES ADM + same-year HD. Fixed institution cohort, stable control, 11 valid yields. Bands = interquartile range.',ys)
''')
md('''## 6 · What CDS adds: the waitlist funnel
IPEDS does not provide these C2 waitlist counts. The CDS layer retains exact documents, page locations and reporting scope. Compare admissions from the waitlist with students accepting a waitlist place; this is not the probability for every waitlisted applicant, and schools do not use identical waitlist procedures.''')
code('''
c=cds[cds.section.eq('C2')&cds.gender.eq('total')&cds.residency.eq('all')&cds.population.eq('first_time_first_year')&cds.cohort_year.isin([2023,2024])]
w=c.pivot(index=['unitid','cohort_year','school'],columns='metric',values='value').reset_index()
for col in ['waitlist_accepted','waitlist_admitted']: w[col]=pd.to_numeric(w[col],errors='coerce')
w=w[(w.waitlist_accepted>=100)&w.waitlist_admitted.notna()]
w=w.sort_values('cohort_year').groupby('unitid',as_index=False).tail(1)
w['waitlist_admit_pct']=100*w.waitlist_admitted/w.waitlist_accepted
assert w.waitlist_admit_pct.between(0,100).all()
w=w.nlargest(16,'waitlist_accepted').sort_values('waitlist_admit_pct')
fig,ax=plt.subplots(figsize=(12,8.5));y=np.arange(len(w))
ax.barh(y,w.waitlist_admit_pct,color=TEAL,height=.62)
ax.set_yticks(y,labels=[textwrap.fill(f'{r.school} · {int(r.cohort_year)}',36) for r in w.itertuples()]);ax.tick_params(axis='y',length=0,pad=9)
ax.set(xlabel='Admitted from waitlist / accepting a waitlist place (%)',xlim=(0,max(10,w.waitlist_admit_pct.max()*1.3)));ax.grid(axis='x');ax.set_axisbelow(True)
for i,r in enumerate(w.itertuples()): ax.text(r.waitlist_admit_pct+.3,i,f'{r.waitlist_admit_pct:.1f}%   {int(r.waitlist_admitted):,}/{int(r.waitlist_accepted):,}',va='center',fontsize=8)
caption=f'Among these {len(w)} sourced CDS school-years, the conditional waitlist admission share ranges from {w.waitlist_admit_pct.min():.1f}% to {w.waitlist_admit_pct.max():.1f}%; counts and source scope are essential to interpretation.'
finish(fig,'06_cds_waitlists','The waitlist is a different admissions funnel',caption,
 'Source: official CDS C2. Latest 2023/2024 available per school; ≥100 acceptances. Largest 16 accepting cohorts.',w)
''')
md('''## Continue from here
Join tables on `unitid` and `cohort_year`. Use `institutions.csv` for the most recent available directory profile, and the panel's same-year HD fields for historical comparisons. Start with `validation/` before expanding a comparison; a blank is never a zero.

Scores describe submitters; SAT definitions changed during the decade. NCES policy categories also changed, so use the annual variable mapping rather than treating a numeric code as a stable policy. No SAT composite percentile is constructed by summing section percentiles. CDS and IPEDS differences remain in `validation/v2/consistency.csv` inside `validation.zip`.

Sources: [NCES IPEDS downloads](https://nces.ed.gov/ipeds/use-the-data/download-access-database), [annual collection materials](https://nces.ed.gov/ipeds/use-the-data/download-survey-material), and exact university CDS URLs in `sources.csv`. Federal IPEDS data are public domain; university source documents retain their own rights. Compilation and original code: CC BY 4.0. This notebook and its attached dataset are private review drafts.''')
code('''
assert len(charts)==6
(OUT/'analysis_summary.json').write_text(json.dumps({'facts':facts,'figures':charts,'dataset_path':str(DATA),'status':'completed','figure_count':len(charts)},indent=2))
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>A decade of US college admissions</title><style>body{background:#faf9f5;color:#183247;font:17px/1.6 system-ui;max-width:1050px;margin:65px auto;padding:0 28px}h1{font-size:42px;line-height:1.1}h2{margin-top:65px;font-size:28px}img{width:100%}.small{font-size:13px;color:#546874}.tag{color:#087f8c;letter-spacing:2px;font-size:13px}section{margin-bottom:60px}p{max-width:850px}</style><body><p class="tag">IPEDS + COMMON DATA SET · PRIVATE REVIEW DRAFT</p><h1>A decade of US college admissions</h1>']
parts.append('<p>'+f"{facts['institutions']:,} institutions · {facts['institution_years']:,} observed institution-years · 2014–2024"+'</p>')
parts.append('<p class="small">All findings are descriptive. Exact filters, source tables and reproducible code are in the accompanying notebook. No applicant-level probability or causal policy claim is made.</p>')
for ch in charts:
    b64=base64.b64encode((FIG/(ch['slug']+'.svg')).read_bytes()).decode()
    parts.append('<section><h2>'+html.escape(ch['title'])+'</h2><p>'+html.escape(ch['caption'])+'</p><img alt="'+html.escape(ch['title'])+'" src="data:image/svg+xml;base64,'+b64+'"><p class="small">'+html.escape(ch['footnote'])+'</p></section>')
parts.append('<p class="small">Sources: NCES IPEDS ADM and same-year HD, 2014–2024; official university Common Data Sets with exact source URLs in the dataset. See DATA_DICTIONARY.md and validation/ for definitions, flags, coverage and preserved disagreements.</p></body></html>')
(OUT/'starter_reader.html').write_text(''.join(parts))
print(json.dumps({'status':'completed','figures':len(charts),'institution_years':len(p)},indent=2))
''')

# Narrower left margins need to be applied after the common layout helper.
for cell in cells:
    if cell.cell_type == 'code':
        cell.source = cell.source.replace("fig.subplots_adjust(left=.11,right=.95,top=.84,bottom=.15)",
            "fig.subplots_adjust(left=.40 if slug in ['02_rate_changes','06_cds_waitlists'] else .11,right=.95,top=.84,bottom=.15)")
nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}, 'language_info':{'name':'python','version':'3.11'}})
nbf.validate(nb)
DEST.mkdir(exist_ok=True)
nbf.write(nb, DEST/'admissions_starter.ipynb')
metadata={'id':'yangkuangou/a-decade-of-us-college-admissions-ipeds-cds',
    'title':'A decade of US college admissions: IPEDS + CDS',
    'code_file':'admissions_starter.ipynb','language':'python','kernel_type':'notebook',
    'is_private':True,'enable_gpu':False,'enable_internet':False,
    'dataset_sources':['yangkuangou/us-college-admissions-panel-ipeds-cds-2014-2024'],
    'competition_sources':[],'kernel_sources':[],'keywords':['education','data visualization','exploratory data analysis']}
(DEST/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(f'Wrote {len(cells)} cells; all code syntax and notebook schema validated')

if __name__=='__main__': pass
