"""Write the final handoff from saved receipts and observed outputs."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return list(csv.DictReader((ROOT/p).open(encoding='utf-8-sig')))
def j(p,default=None):
    path=ROOT/p
    return json.loads(path.read_text()) if path.exists() else default
def main():
    s=j('validation/v2/integration_summary.json');ips=j('validation/ipeds_v2_summary.json')
    cs=j('validation/summary.json');analysis=j('notebook_v2/outputs/analysis_summary.json',{})
    meta=j('receipts/v2/dataset_metadata_after/dataset-metadata.json',{})
    meta=meta.get('info',meta)
    rt=j('receipts/v2/roundtrip_verification.json',{})
    privacy=j('receipts/v2/privacy_verification.json',{})
    table='\n'.join(f"|{r['year']}|{r['adm_rows']}|{r['complete_c1_triples']}|{r['matched_same_year_hd']}|" for r in ips['by_year'])
    r=read('data/cds_long.csv');sections=[]
    for code in ['C1','C2','C9','C10','C11/C12','H2','B1']:
        q=[x for x in r if x['section'] in code.split('/')]
        sections.append(f"|{code}|{len({x['unitid'] for x in q})}|{len({(x['unitid'],x['cohort_year']) for x in q})}|{len(q)}|")
    rate=meta.get('usabilityRating')
    usability=f"{10*rate:.2f}/10（服务器原值 {rate}）" if rate is not None else '未取得服务器分值，不声称10/10'
    columns=len(next(csv.reader((ROOT/'data/ipeds_admissions_panel.csv').open())))
    report=f'''# cds_v2 交付报告

核验日期：2026-10-26。工作目录：`{ROOT}`。

## 本轮交付

- **IPEDS：{s['ipeds_institutions']:,} 个唯一 UNITID、{s['ipeds_institution_years']:,} 个校年、{columns} 列，2014–2024 全部11年。** 每一官方 ADM 行均保留；不是仅选31校，也没有补出不存在的行。
- **CDS：{s['cds_schools']} 所、{s['cds_school_years']} 个校年、{s['cds_observations']:,} 条数值观察。** 2023/2024 至少一年有数据：{s['cds_2023_2024_schools']} 所；**两年都齐：{s['cds_schools_both_2023_2024']} 所**。因此不能把学校总数说成完整的60校×2年矩阵。原 v1 的 {s['v1_observations_preserved']} 条数值均逐键保留。
- [私有数据集](https://www.kaggle.com/datasets/yangkuangou/us-college-admissions-panel-ipeds-cds-2014-2024)。原 v1 保留，未改公开状态；新 slug 与2014–2024范围匹配。
- [私有 starter notebook](https://www.kaggle.com/code/yangkuangou/a-decade-of-us-college-admissions-ipeds-cds)。运行状态/隐私以本报告回执段为准；六图源码和读者页在下方路径。
- Kaggle CLI 限 title≤50字符，采用 `US College Admissions Panel 2014–2024: IPEDS + CDS`。完整数据定位在描述首段；描述含3个分析入口、5行读取示例、字段表、来源及许可。封面是原生排版图，已目视核对全图和中心裁切范围。

## 交付路径

| 产物 | 绝对路径 |
|---|---|
| IPEDS主表 | `{ROOT}/data/ipeds_admissions_panel.csv` |
| 院校最新可得档案 | `{ROOT}/data/institutions.csv` |
| CDS权威长表 | `{ROOT}/data/cds_enrichment_long.csv` |
| CDS宽表 | `{ROOT}/data/cds_enrichment_wide.csv` |
| 字典 | `{ROOT}/DATA_DICTIONARY.md` |
| 全部来源 | `{ROOT}/sources.csv` |
| 校验/覆盖/差异 | `{ROOT}/validation/` |
| IPEDS原变量映射 | `{ROOT}/validation/ipeds_variable_mapping.csv` |
| 冻结上传包 | `{ROOT}/kaggle_v2/` |
| Starter源码 | `{ROOT}/notebook_v2/admissions_starter.ipynb` |
| 六图/图表原始数据/读者HTML | `{ROOT}/notebook_v2/outputs/` |
| 上传、运行、隐私、回读回执 | `{ROOT}/receipts/v2/` |

上传目录顶层预览六份 CSV，`validation.zip` 内保留原目录结构；本轮权威差异表在 `validation/v2/consistency.csv`。`reproducibility.zip` 包含官方 IPEDS 原表、获取/合并/打包代码、冻结 CDS 分表及 v1 数值核验基线，不含大学原始 PDF 的再分发。

## 年份骨架

| Fall year | ADM报告行 | 完整C1总数三元组 | 同年HD匹配 |
|---|---:|---:|---:|
{table}

22张官方ADM/HD来源表均有官方URL、release状态、归档成员和SHA-256。2014–2023取到final/revised，2024是provisional。{ips['matched_hd_rows']:,}/{ips['reporter_rows']:,} 行匹配同年HD，{ips['complete_c1_triples']:,} 行有完整C1三元组。主表保留历年学校名、州/辖区、control、Carnegie分类、经纬度；institutions表仅作最新可得快照，`metadata_year` 明确标年。未做可选EF/SFA扩表，避免扩大非必要范围。

ADM不是所有美国高校普查；开放录取且不报ADM的机构不在骨架内。学校关闭、合并、分校变化会导致非平衡覆盖；稳定UNITID也不保证范围不变。申请量是院校层面的申请，不是全国去重申请人数。

## CDS字段实际覆盖

| 分组 | 学校数 | 校年数 | 观察数 |
|---|---:|---:|---:|
{chr(10).join(sections)}

学校集合含研究型大学与知名文理学院，不宣称复现某届排名前60。保留v1的2019–2025稀疏CDS观测，本轮优先2023/2024；标题的2014–2024对应IPEDS骨架，不表示CDS也覆盖十一年。未核验原件或表格上下文的记录继续排除，不把IPEDS数值填入CDS。

## 关键质量决定和已知限制

1. **考试政策实际断点是2022。** 11份NCES原始Access字典已逐年核验，`validation/ipeds_v2_policy_codes.csv` 保留精确标签、URL、SHA与工作表行。2014–15含Do not know；2016–21加入Considered but not required；2022–24才明确Test Optional/Test Blind。同一code3不可直接跨断点解释。主表逐行给字典URL/hash。早期“仅2024变义”的调查假设已纠正。
2. **SAT口径变化。** 2014–2016 critical reading与旧写作列、2017以后EBRW含义分开注释；分位数限于提交者。未将单项分位相加造综合分位。SAT/ACT提交群体重叠，不可将百分比相加。
3. **特殊码与NCES填补。** 负的NCES特殊码转空，但原码JSON保留；原NCES状态/填补旗标保留。未自行插值、补零或新增统计填补，不能把“未自行填补”误读为“NCES每个数均原始实报”。
4. **Purdue 2024来源内部不一致。** 主`admitted`保留官方CDS-C!C42印刷总数30,272；性别22,551+16,721与州籍9,091+25,935+4,246独立求和均39,272，另存`admitted_sum_of_reported_categories`，不代替主值。2024范围扩为West Lafayette+Indianapolis+Polytechnic Statewide。2023入学数也与IPEDS有差异，均保留。
5. **Case Western 2024。** 原表ACT 23%与旁列269人/C1入学1,619不自洽，原百分比保留，原因未证实。Duke2023性别求和不等于总值的旧警告保留。
6. **其他范围差异。** Columbia CDS仅College+Engineering，BC排除指定学院，Middlebury部分指标注明September Only。GPA量表不统一；H2平均grant以受助者为条件；实际资助学年可能早于CDS版本，继续按真实cohort_year保留。缺失绝不当0。
7. **来源访问差异。** 部分PDF网页层漏掉AcroForm值，已用私有CPU取原件再按表单/渲染核对。无法取得原字节但能核实官方PDF表格和物理页的来源明确无hash，不假称完整二进制审计。Brown/Notre Dame/NYU/Georgetown/UPenn及部分PSU来源仍受404/403/405/断连或受限托管阻挡，未用二手数值凑齐。

## 验证与计算

- IPEDS规则错误：{sum(ips.get('issues',{}).values()) if ips.get('issues') else 0}；CDS规则：{cs['rule_errors']} errors / {cs['rule_warnings']} warnings；额外来源矛盾表：`validation/v2/source_inconsistencies.csv`。
- 所有IPEDS校年键、institutions键、CDS自然键唯一；CDS长宽表逐值对照、来源ID关联、v1全部值保留检查通过，见`validation/v2/integration_summary.json`。
- CDS/IPEDS C1逐项状态：`{s['cds_ipeds_status']}`。差异不自动判错、不改原值。Fall2025不在本轮IPEDS骨架内，保持未对照状态。
- 本机仅标准库轻量表格转换、下载回收、必要页面渲染；未本地训练/benchmark或安装数据科学依赖。重任务前资源检查WARN（44–45GB余量、swap约9.5GB），无STOP。所有获取/代码字典/文档恢复与starter执行均为私有Kaggle CPU，无GPU、新费用或公开发布。

## Starter notebook

{len(analysis.get('figures',[]))} 张图完成回收。主题：年度ADM覆盖、固定队列十年录取率下降、固定提交报告队列SAT/ACT变化、申请量增长与录取率变化、固定公立/私立非营利院校yield、CDS waitlist漏斗。每图导出PNG+SVG、底层CSV和一句数据结论；开头3行结论从实际数据计算。固定样本筛选、分母、报告范围和非因果解释均在代码/图注写明。正文为供Leader重写的英文草稿。

实际摘要：`{json.dumps(analysis.get('facts',{}),ensure_ascii=False)}`。

## Kaggle回执与停止状态

- 服务器 dataset ID：`{meta.get('datasetId','未取得')}`；isPrivate：`{meta.get('isPrivate','未取得')}`；usability：**{usability}**。
- 数据集版本/就绪状态：见`receipts/v2/dataset_status.txt`。metadata来源/标签/column descriptions/封面更新回执见`receipts/v2/`，不将本地metadata等同于服务器全部接受。
- 服务器隐私与kernel挂载核验：`{json.dumps(privacy,ensure_ascii=False)}`。
- 下载回读：`{json.dumps(rt,ensure_ascii=False)}`。
- 实际图像与读者页面验收记录：`receipts/v2/visual_review.json`。若浏览器读者界面无法取得，记录具体限制，不冒充已视觉验收网页。
- 本轮只私有上传/私有运行，未公开数据集、未发Discussion、未修改现有公开notebook、未做任何投票交换。Leader可据此审阅数据/图像/差异后决定公开。
'''
    (ROOT/'REPORT.md').write_text(report)
    print('Wrote REPORT.md')
if __name__=='__main__':main()
