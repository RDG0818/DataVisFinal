#!/usr/bin/env python3
"""Create the private, reviewable Kaggle upload package from accepted outputs."""
import csv, hashlib, json, shutil, zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
K=ROOT/"kaggle"
def read(path):
    with (ROOT/path).open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))
def copy(source,target=None):shutil.copyfile(ROOT/source,K/(target or Path(source).name))
def main():
    summary=json.loads((ROOT/"validation/summary.json").read_text())
    assert summary['schools']>=30 and summary['rule_errors']==0
    assert summary['schools_with_ipeds_crosscheck']==summary['schools']
    long=read("data/cds_long.csv");wide=read("data/cds_wide.csv")
    for p in ["data/cds_long.csv","data/cds_wide.csv","sources.csv","DATA_DICTIONARY.md"]:copy(p)
    for p in (ROOT/"validation").glob("*"):
        if p.is_file():copy(str(p.relative_to(ROOT)))
    sectionnames=[("C1","申请/录取/入学"),("C2","Waitlist"),("C9","SAT/ACT"),("C10","高中排名"),("C11/C12","GPA"),("H2","Need-based aid"),("B1","本科总人数")]
    sectrows=[]
    for code,label in sectionnames:
        rr=[r for r in long if r['section'] in code.split('/')]
        sectrows.append(f"|{code} {label}|{len({r['unitid'] for r in rr})}|{len({(r['unitid'],r['cohort_year']) for r in rr})}|{len(rr)}|")
    years=Counter(r['cohort_year'] for r in wide)
    diffs=[r for r in read("validation/consistency.csv") if r['status']=='difference_preserved']
    large=sorted(diffs,key=lambda r:abs(float(r['cds_minus_ipeds'])),reverse=True)[:8]
    diffrows=[f"|{r['school']}|{r['cohort_year']}|{r['metric']}|{r['cds_value']}|{r['ipeds_value']}|{r['cds_minus_ipeds']}|" for r in large]
    report=f"""# cds_panel 交付报告

核验日期：2026-10-26。状态：本地质量门槛通过；Kaggle 上传/隐私/回读回执以 `receipts/` 与本报告末尾为准。

## 交付结果

- **{summary['schools']} 所大学、{summary['school_years']} 个校年、{summary['observations']} 条长表观测**。达到用户允许的 ≥30 校首版门槛，未达到 60 校目标。
- 时间范围 Fall 2019–2025，**非平衡面板**。各年校数：{', '.join(f'{y}: {years[y]}' for y in sorted(years))}。不是 31×7 的完整矩阵；不插值、不填零。
- `data/cds_long.csv`、`data/cds_wide.csv`、`sources.csv`、`DATA_DICTIONARY.md`、`validation/`、Kaggle 可上传目录 `kaggle/`。Kaggle 目录为了直接预览 CSV，将两张主表放在顶层。
- 31 个 UNITID 均在直接下载的官方 HD2024 中存在；见 `validation/institution_identity.csv`。
- 全部接受记录已核对官方表格上下文和页码/工作表/HTML 位置。可下载的 14 份 CDS 原始文件均已校验 SHA-256；其他官方 PDF 用网页渲染/索引表审读，未声称有原始 PDF 哈希。Google 托管来源的校方链接链路在 sources 与分片说明中保留。

## 字段实际覆盖

|字段组|学校数|校年数|观测数|
|---|---:|---:|---:|
{chr(10).join(sectrows)}

C7 可选因素尚未采集。C1 每一接受校年都有总申请/总录取/总入学；性别和州别只保留真实已报告分项，不补齐。C9、GPA、H2 等覆盖明显较少，不能将标题年份或空列理解为全覆盖。UC 未报告测试数据时保持缺失。原先 13 篇 notebook 未全部纳入：Brown/Northwestern 等仍有页码核验缺口，UW/Purdue 等本轮未完成可信统一提取；没有为凑齐学校而填入外部估计。

## 采集与复现

1. 优先使用 Berkeley 官方链接的 Google Sheets/XLSX；可下载 PDF 使用 `pdftotext` 加表格规则与人工上下文复核；不可直接下载的官方 PDF 使用可访问的官方网页渲染表。USC/MIT 使用校方 HTML。实际方法逐条保留在 `extraction_method`，没有将手工转录标成全自动。
2. 三个分片脚本见 `shards/private/`、`shards/public/`、`shards/more/`。OpenCDS 仅作来源发现，未核对的二手数值未纳入。可追溯原值在分片 CSV；总表不引用 IPEDS 填缺。
3. `python3 scripts/build_panel.py` 只用 Python 标准库即可合并与核验现有分片。`python3 scripts/package_dataset.py` 重新打包。本地安装尝试因网络停滞已停止；未依赖未安装成功的库来声称完成提取。
4. 本机只做轻量下载、文件解析与校验；NCES 下载移到两个**私有 Kaggle CPU** 工具任务，没有 GPU 或新费用。第一个获取 ADM2019–2023，第二个从官方 2024–25 Provisional Access ZIP 提取 ADM2024 与 HD2024；两个均 COMPLETE，回执在 `receipts/`。未重复发送等价计算。
5. `reproducibility.zip` 包含冻结分片、合并脚本、来源目录、官方 IPEDS 参考表和采集回执 JSON。完整大学原始 PDF 保留本地 `raw/`，不将其版权自动纳入本数据集许可。

## 规则校验与第三方交叉核验

- 数值：申请 ≥ 录取 ≥ 入学、非负整数、百分比范围、SAT/ACT 合法范围与分位单调、waitlist 计数顺序、排名累计比例和财助子集顺序。结果 **0 errors / 1 warning**。
- 唯一性：长表自然键与宽表校年键唯一；宽表每个已填字段带 source_id/page/method/review status 的 JSON provenance。长宽表值在打包前逐字段比对。
- 警告：Duke 2023 申请总数 46,366 与可见性别分项 46,333 相差 33。保留总值与分项，不假设缺失性别为零。见 `issues.csv`。
- **31/31 校至少一个同年 C1 triple 已与官方 NCES IPEDS ADM 对照**；不是所有年份都能对照。216 个总数比较中：132 exact match、60 difference preserved、24 not available（Fall 2025 未获得 ADM 参考表）。差异不等于错误，仍需考虑不同报告版本、窗口和人群；未证实原因的保留为未知。
- 所有差异/空缺在 `validation/consistency.csv`，所有 IPEDS 直接官方获取地址、表名、时间、哈希在 `validation/ipeds_sources.csv`。旧 ADM2024/2025 URL 的 404 失败证据保留；后来已通过官方 Access release 成功取得 ADM2024，未把 404 误写为数据不存在。

较大差异样例（CDS 原值未改）：

|学校|年份|指标|CDS|IPEDS|CDS−IPEDS|
|---|---:|---|---:|---:|---:|
{chr(10).join(diffrows)}

UCR2023、UNC2022 和 Emory2023 的较大差异已回看官方 C1 表仍相同，原因未证实。Columbia CDS 只覆盖 Columbia College + Engineering，与 UNITID 整体有范围差异；Boston College 明确排除 Messina/Woods。Rochester C1 含 Eastman，C9 若只含 AS&E 则未合并。Purdue 近年校园范围变化未强行统一。具体说明在逐字段 notes 与分片 README。

H2 按实际资助学年归位：Harvard 的 2024–25 CDS 报告 2023–24 final，放在 cohort_year=2023；UNC 的 2023–24 CDS 报告 2022–23 final，放在 2022。H2-D 任何财助人数与 H2-E need-based grant 人数分开，H2-K 是受助者平均 grant。当前 estimated 与 final 不混称最终值。

## 排除与限制

- {summary['excluded_observations']} 条原始提取保留在 `validation/excluded_observations.csv`，主要是物理页码未核实的 Brown/Dartmouth/Northwestern、部分 Princeton/Stanford/Cornell 年份与 Penn State。它们不计入 31 校与主表指标。
- UCSB 2023 原 PDF A0 标明校内 IR 与校方 CDS 页面，历史 Drive 链接在当前落地页不再显示，来源链路弱于 2025，已明确标记。
- 评分提交者不是全体新生；SAT 综合分位没有用两个单项分位相加。GPA 量表不统一（有 >4 的加权 GPA），不得直接跨校排名。平均 grant 是受助者条件均值，不是所有学生平均净价。
- 学校集合为本轮可核实的知名院校，不宣称严格复现某一届 US News 前 60 排名名单。数据描述机构已发生的录取，不能预测个体申请概率。

## 扩展到 ≥60 校的剩余计划

1. 先补 Brown、Dartmouth、Northwestern 的原始 PDF/物理页码，Penn State 的可打开版本，以及 UPenn 的官方 Box 文件；对新加入校完成同年 IPEDS 对照。
2. 再补 UW Seattle、Purdue（分开旧/新统计范围）、Wisconsin、UIUC、Georgia Tech、UT Austin、Notre Dame、Georgetown、Vanderbilt、WashU、Maryland、NYU 等，随后按实际名单补足至少 29 所，不靠低质条目凑 60。
3. 对现有学校优先补 2019–2022 与 2025 缺年（31×7 共 217 格，本版只有 72 格），再扩 C9/B1/C10/GPA/H2 的覆盖。C7 留到主指标稳定后。
4. 公开前由 Leader 审查来源链路、最大差异、报告范围和真实 Kaggle 读者界面；此次授权只私有，未发布 Discussion、未改现有公开 notebook，也未进行任何投票交换。

## Kaggle 上传与隐私回执

具体上传结果由 `receipts/dataset_create.txt`、`receipts/dataset_status.txt`、`receipts/remote_metadata/`、`receipts/roundtrip_verification.json` 给出。此段由最终上传核验后追加。
"""
    (ROOT/"REPORT.md").write_text(report)
    copy("REPORT.md")
    md=f"""# US College Admissions: Common Data Set Panel 2019–2025

**{summary['schools']} schools · {summary['school_years']} school-years · {summary['observations']} source-preserving observations**

Compare institutional admissions, waitlists, score-submitter distributions, enrollment and selected need-based aid data using official university Common Data Sets. This is an **unbalanced** panel, not complete coverage of every field or every year.

Start with `cds_wide.csv` for exploration, or `cds_long.csv` for exact populations and field-level source URLs, pages and methods. All {summary['schools']} schools have at least one same-year C1 cross-check against directly acquired official NCES IPEDS ADM. Reported differences stay visible in `consistency.csv`; no CDS value is overwritten, imputed or interpolated.

| File | Use |
|---|---|
| `cds_long.csv` | One sourced numeric observation per metric and population |
| `cds_wide.csv` | One institution and entering-fall year per row, with JSON provenance |
| `sources.csv` | Exact official documents, locations, acquisition methods and available hashes |
| `DATA_DICTIONARY.md` | Definitions, units, denominators and temporal alignment |
| `coverage.csv`, `metric_coverage.csv` | Actual coverage and missing fields |
| `consistency.csv`, `issues.csv` | IPEDS discrepancies and numerical rule findings |
| `reproducibility.zip` | Frozen source observations, build scripts and official IPEDS reference CSVs |
| `REPORT.md` | Detailed Chinese acceptance report and plan to reach 60 schools |

Admission rate = admitted / applicants; yield = enrolled / admitted, with matching populations. Scores describe submitters, GPA scales vary, and aid means describe recipients. Columbia's CDS covers College + Engineering; Boston College excludes specified colleges. Aid cohorts follow the aid academic year, which may differ from the CDS edition. See row notes before comparing institutions or years.

Compilation and original code: CC BY 4.0, attribution to yangkuangou and the listed institutions. Underlying university documents retain their own rights; this license does not relicense those documents or imply institutional endorsement. Federal IPEDS reference data are identified separately.

This upload is a **private review version**. Public release is reserved for the project Leader.
"""
    (K/"README.md").write_text(md)
    desc=md.replace('# US College Admissions: Common Data Set Panel 2019–2025\n','',1)
    metadata={"title":"US College Admissions: CDS Panel 2019-2025",
        "id":"yangkuangou/us-college-admissions-cds-panel-2019-2025",
        "subtitle":f"{summary['schools']} schools, official CDS sources, tidy and wide tables, IPEDS checks",
        "description":desc,"licenses":[{"name":"CC-BY-4.0"}],"keywords":["education"],
        "isPrivate":True,"image":"cover.png","userSpecifiedSources":"Official university Common Data Sets; exact per-value source URLs and pages in cds_long.csv and sources.csv. Official NCES IPEDS ADM2019-2024; acquisition URLs and SHA256 in ipeds_sources.csv.","resources":[]}
    field_descriptions={"school":"Reporting school display name; see notes for institutional scope", "unitid":"NCES IPEDS institution identifier", "cohort_year":"Actual entering-fall or first-year aid cohort year", "cds_edition":"Source CDS academic-year edition; can differ from aid cohort", "metric":"Stable semantic measurement name; see DATA_DICTIONARY.md", "population":"Exact denominator population", "gender":"Reported category; absent category is not zero", "residency":"Reported residency category", "value":"Numeric source value; no imputation", "unit":"count, percent (0-100), score, gpa or usd", "source_id":"Join key to sources.csv", "source_url":"Exact official source URL", "page":"Physical PDF page (1-based), worksheet/cell or HTML section", "extraction_method":"Actual extraction or explicit derivation method", "verification_status":"Source table-context review flag", "rule_validation":"Implemented numeric rule check result", "ipeds_c1_check":"Same-school-year C1 triple comparison, not a check of every field", "notes":"Reporting scope, aid year, derivation operands and other source caveats", "source_urls":"JSON array of documents used", "field_provenance":"JSON map of each metric field to source/page/method/review status"}
    for filename,description in [("cds_long.csv","Authoritative tidy observations with per-value provenance"),("cds_wide.csv","One row per school and actual entering-fall year"),("sources.csv","Official source document registry"),("consistency.csv","Same-year C1 comparison with official IPEDS; differences retained")]:
        with (K/filename).open(newline="") as f:header=next(csv.reader(f))
        def dtype(c):
            if c in ['unitid','cohort_year']:return 'integer'
            if c in ['value','cds_value','ipeds_value','cds_minus_ipeds']:return 'number'
            if filename=='cds_wide.csv' and c not in ['school','cds_edition','ipeds_c1_check','rule_validation','source_urls','field_provenance']:return 'number'
            return 'string'
        metadata['resources'].append({"path":filename,"description":description,"schema":{"fields":[{"name":c,"description":field_descriptions.get(c,"See DATA_DICTIONARY.md; population suffixes are part of the field definition"),"type":dtype(c)} for c in header]}})
    (K/"dataset-metadata.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n")
    # No university original PDFs or full document text are redistributed.
    paths=[ROOT/"SHARD_CONTRACT.md",ROOT/"sources.csv",ROOT/"DATA_DICTIONARY.md",ROOT/"scripts/build_panel.py",ROOT/"scripts/package_dataset.py"]
    paths+=list((ROOT/"shards").glob("*/*.csv"))+list((ROOT/"shards").glob("*/README.md"))
    paths += [ROOT/"shards/private/compile_observations.py",ROOT/"shards/private/extract_harvard.py",ROOT/"shards/public/build.py",ROOT/"shards/more/extract_reviewed.py"]
    paths+=list((ROOT/"raw/ipeds/remote").glob("*.csv"))+list((ROOT/"raw/ipeds/newer_remote").glob("*.csv"))
    paths += [ROOT/"raw/ipeds/remote/ipeds_acquisition.json",ROOT/"raw/ipeds/newer_remote/official_newer_acquisition.json",ROOT/"validation/ipeds_sources.csv"]
    paths+=list((ROOT/"scripts/ipeds_remote").glob("*.py"))+list((ROOT/"scripts/ipeds2024_remote").glob("*.py"))
    with zipfile.ZipFile(K/"reproducibility.zip","w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(paths)):
            if p.exists():z.write(p,str(p.relative_to(ROOT)))
    manifest={p.name:{"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(K.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (K/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"files":len(manifest),"bytes":sum(r['bytes'] for r in manifest.values()),"private":metadata['isPrivate'],"title_length":len(metadata['title'])},indent=2))
if __name__=='__main__':main()
