"""Build the all-reporter 2014–2024 IPEDS ADM panel from official NCES CSVs.

This deliberately preserves survey rows, absent cells, year-specific HD metadata,
original variable mappings and NCES status flags. It uses the Python standard library.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'raw/ipeds_v2'
DATA = ROOT / 'data'
VALIDATION = ROOT / 'validation'

EXISTING = {
    **{('ADM', y): ROOT / f'raw/ipeds/remote/ADM{y}_official.csv' for y in range(2019, 2024)},
    ('ADM', 2024): ROOT / 'raw/ipeds/newer_remote/ADM2024_official.csv',
    ('HD', 2024): ROOT / 'raw/ipeds/newer_remote/HD2024_official.csv',
}
OLD_SOURCE_FILE = ROOT / 'validation/ipeds_sources.csv'
ACQUISITION_FILE = RAW / 'acquisition_manifest.json'

COUNT_VARS = {
    'APPLCN': 'applicants', 'APPLCNM': 'applicants_men',
    'APPLCNW': 'applicants_women', 'APPLCNAN': 'applicants_another_gender',
    'APPLCNUN': 'applicants_gender_unknown',
    'ADMSSN': 'admitted', 'ADMSSNM': 'admitted_men',
    'ADMSSNW': 'admitted_women', 'ADMSSNAN': 'admitted_another_gender',
    'ADMSSNUN': 'admitted_gender_unknown',
    'ENRLT': 'enrolled', 'ENRLM': 'enrolled_men',
    'ENRLW': 'enrolled_women', 'ENRLAN': 'enrolled_another_gender',
    'ENRLUN': 'enrolled_gender_unknown',
    'ENRLFT': 'enrolled_full_time', 'ENRLFTM': 'enrolled_full_time_men',
    'ENRLFTW': 'enrolled_full_time_women',
    'ENRLFTAN': 'enrolled_full_time_another_gender',
    'ENRLFTUN': 'enrolled_full_time_gender_unknown',
    'ENRLPT': 'enrolled_part_time', 'ENRLPTM': 'enrolled_part_time_men',
    'ENRLPTW': 'enrolled_part_time_women',
    'ENRLPTAN': 'enrolled_part_time_another_gender',
    'ENRLPTUN': 'enrolled_part_time_gender_unknown',
    'SATNUM': 'sat_submit_count', 'ACTNUM': 'act_submit_count',
}
PCT_VARS = {'SATPCT': 'sat_submit_pct', 'ACTPCT': 'act_submit_pct'}
SCORE_PREFIX = {
    'SATVR': 'sat_reading', 'SATMT': 'sat_math', 'SATWR': 'sat_writing',
    'ACTCM': 'act_composite', 'ACTEN': 'act_english',
    'ACTMT': 'act_math', 'ACTWR': 'act_writing',
}
SCORE_VARS = {f'{raw}{q}': f'{name}_p{q}'
              for raw, name in SCORE_PREFIX.items() for q in ('25', '50', '75')}
CONSIDERATIONS = {
    1:'secondary_school_gpa_policy_code',2:'secondary_school_rank_policy_code',
    3:'secondary_school_record_policy_code',4:'college_preparatory_program_policy_code',
    5:'recommendations_policy_code',6:'formal_competency_demonstration_policy_code',
    7:'admission_test_score_policy_code',8:'english_proficiency_test_policy_code',
    9:'other_admission_test_policy_code',10:'work_experience_policy_code',
    11:'personal_statement_or_essay_policy_code',12:'legacy_status_policy_code',
}
ADM_VARS = {**COUNT_VARS, **PCT_VARS, **SCORE_VARS,
            **{f'ADMCON{i}': name for i,name in CONSIDERATIONS.items()}}
HD_VARS = {
    'INSTNM': 'institution_name', 'CITY': 'city', 'STABBR': 'state',
    'CONTROL': 'control_code', 'SECTOR': 'sector_code',
    'ICLEVEL': 'institution_level_code', 'LOCALE': 'locale_code',
    'C21BASIC': 'carnegie_2021_basic_code',
    'C18BASIC': 'carnegie_2018_basic_code',
    'C15BASIC': 'carnegie_2015_basic_code',
    'CCBASIC': 'carnegie_2005_basic_code',
    'CARNEGIE': 'carnegie_2000_code',
    'C00CARNEGIE': 'carnegie_2000_code',
    'CARNEGIEIC': 'carnegie_institutional_classification_code',
    'LONGITUD': 'longitude', 'LATITUDE': 'latitude',
}
CONTROL = {'1': 'Public', '2': 'Private nonprofit', '3': 'Private for-profit'}
NEGATIVE_CODES = {'-1', '-2', '-3', '-4', '-5', '-6', '-9'}


def csv_rows(path: Path):
    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        yield reader.fieldnames or [], reader


def decode_official(path: Path):
    data = path.read_bytes()
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('cp1252')


def sha(path: Path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def json_cell(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) if obj else ''


def numeric(raw: str, *, real=False):
    value = (raw or '').strip()
    if not value or value in NEGATIVE_CODES:
        return ''
    if real:
        try:
            n = float(value)
            return value if n == n and n != float('inf') and n != float('-inf') else ''
        except ValueError:
            return ''
    try:
        n = int(value)
    except ValueError:
        return ''
    return str(n) if n >= 0 else ''


def rate(numerator: str, denominator: str):
    if not numerator or not denominator or int(denominator) <= 0:
        return ''
    return f'{int(numerator) / int(denominator):.6f}'


def source_manifest():
    old = {}
    with OLD_SOURCE_FILE.open(newline='') as f:
        for row in csv.DictReader(f):
            if row.get('direct_NCES_acquisition_verified') == 'True':
                old[(row['table'][:2] if row['table'].startswith('HD') else 'ADM',
                     int(row['cohort_year']))] = row
    new = {x['table']: x for x in json.loads(ACQUISITION_FILE.read_text())}
    out = []
    for component in ('ADM', 'HD'):
        for year in range(2014, 2025):
            table = f'{component}{year}'
            path = EXISTING.get((component, year), RAW / f'{table}_official.csv')
            if not path.is_file():
                raise FileNotFoundError(path)
            if (component, year) in old:
                prev = old[(component, year)]
                url = prev['official_source_url']
                expected = prev['sha256']
                release = 'provisional' if year == 2024 else 'final'
                member = prev['archive_member']
                retrieved = prev['retrieved_at']
            else:
                prev = new[table]
                if prev['status'] != 'downloaded':
                    raise ValueError(f'{table} acquisition failed: {prev}')
                url = prev['source_url']
                expected = prev['csv_sha256']
                release = 'final'
                member = prev['archive_member']
                retrieved = prev['retrieved_at']
            actual = sha(path)
            if actual != expected:
                raise ValueError(f'{table} hash mismatch: {actual} != {expected}')
            out.append({'source_id': f'nces_{table.lower()}_{release}',
                        'table': table, 'year': year, 'cohort_year': year,
                        'component': component, 'source_url': url,
                        'official_source_url': url,
                        'release': release, 'release_status': release,
                        'local_path': str(path.relative_to(ROOT)),
                        'sha256': actual, 'archive_member': member,
                        'retrieved_at': retrieved})
    return out


def build():
    policy_codes = {}
    with (VALIDATION / 'ipeds_v2_policy_codes.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            policy_codes[int(r['year']), r['code']] = r
    if len({year for year, _ in policy_codes}) != 11:
        raise ValueError('All 11 official ADMCON7 annual codebooks are required')
    sources = source_manifest()
    source_by_key = {(r['component'], r['year']): r for r in sources}
    hd_by_year: dict[int, dict[str, dict]] = {}
    hd_columns_by_year = {}
    for year in range(2014, 2025):
        path = ROOT / source_by_key['HD', year]['local_path']
        with io.StringIO(decode_official(path), newline='') as f:
            reader = csv.DictReader(f)
            header = [h.strip().upper() for h in reader.fieldnames or []]
            hd_columns_by_year[year] = header
            rows = {}
            for item in reader:
                item = {k.strip().upper(): (v or '').strip() for k, v in item.items()}
                uid = item.get('UNITID', '')
                if uid:
                    if uid in rows:
                        raise ValueError(f'Duplicate HD UNITID {uid}, {year}')
                    rows[uid] = item
            hd_by_year[year] = rows

    panel = []
    adm_columns_by_year = {}
    issues = []
    yearly = []
    for year in range(2014, 2025):
        path = ROOT / source_by_key['ADM', year]['local_path']
        seen = set()
        matched_hd = 0
        with io.StringIO(decode_official(path), newline='') as f:
            reader = csv.DictReader(f)
            adm_columns_by_year[year] = [h.strip().upper() for h in reader.fieldnames or []]
            for item in reader:
                item = {k.strip().upper(): (v or '').strip() for k, v in item.items()}
                uid = item.get('UNITID', '')
                if not uid:
                    raise ValueError(f'ADM{year} missing UNITID')
                if uid in seen:
                    raise ValueError(f'Duplicate ADM UNITID {uid}, {year}')
                seen.add(uid)
                hd = hd_by_year[year].get(uid, {})
                matched_hd += bool(hd)
                rec = {'unitid': uid, 'cohort_year': str(year),
                       'adm_release': source_by_key['ADM', year]['release'],
                       'adm_source_url': source_by_key['ADM', year]['source_url'],
                       'hd_source_url': source_by_key['HD', year]['source_url'],
                       'has_matching_hd': '1' if hd else '0'}
                exceptions = {}
                for original, field in ADM_VARS.items():
                    value = item.get(original, '')
                    if original.startswith('ADMCON'):
                        rec[field] = value if value and value not in NEGATIVE_CODES else ''
                    else:
                        rec[field] = numeric(value)
                    if value in NEGATIVE_CODES:
                        exceptions[original] = value
                    elif value and not rec[field]:
                        exceptions[original] = value
                for original, field in HD_VARS.items():
                    value = hd.get(original, '')
                    if not value and field in rec and rec[field]:
                        continue  # Older CARNEGIE and newer C00CARNEGIE share one meaning.
                    if field in ('longitude', 'latitude'):
                        rec[field] = numeric(value, real=True)
                    elif field.endswith('_code'):
                        rec[field] = value if value and value not in NEGATIVE_CODES else ''
                    else:
                        rec[field] = value
                    if value in NEGATIVE_CODES:
                        exceptions[f'HD:{original}'] = value
                rec['control_label'] = CONTROL.get(rec['control_code'], '')
                policy = rec['admission_test_score_policy_code']
                rec['test_policy_code'] = policy
                policy_ref = policy_codes.get((year, policy), {})
                if policy and not policy_ref:
                    raise ValueError(f'ADMCON7 code {policy} lacks official dictionary for {year}')
                rec['test_policy_label'] = policy_ref.get('label', '')
                rec['test_policy_era'] = ('revised_three_category' if
                                          'Not considered for admission' in
                                          policy_codes[year, '3']['label'] else
                                          'original_four_category')
                rec['test_policy_codebook_url'] = policy_ref.get('source_url', '')
                rec['test_policy_codebook_sha256'] = policy_ref.get('source_sha256', '')
                rec['sat_reading_definition'] = ('SAT critical reading (old scale)' if year <= 2016
                                                 else 'SAT evidence-based reading and writing (new scale)')
                rec['admit_rate'] = rate(rec['admitted'], rec['applicants'])
                rec['yield_rate'] = rate(rec['enrolled'], rec['admitted'])
                rec['ipeds_status_flags_json'] = json_cell({k: v for k, v in item.items()
                                                           if k.startswith('X') and v})
                rec['special_value_codes_json'] = json_cell(exceptions)
                if hd:
                    if rec['state'] and len(rec['state']) != 2:
                        issues.append({'unitid': uid, 'year': year, 'rule': 'state_code_length',
                                       'severity': 'warning', 'detail': rec['state']})
                for left, right in [('admitted', 'applicants'), ('enrolled', 'admitted')]:
                    if rec[left] and rec[right] and int(rec[left]) > int(rec[right]):
                        issues.append({'unitid': uid, 'year': year, 'rule': 'count_order',
                                       'severity': 'error', 'detail': f'{left}>{right}'})
                if all(rec[x] for x in ('enrolled', 'enrolled_full_time', 'enrolled_part_time')):
                    if int(rec['enrolled_full_time']) + int(rec['enrolled_part_time']) != int(rec['enrolled']):
                        issues.append({'unitid': uid, 'year': year, 'rule': 'enrollment_attendance_sum',
                                       'severity': 'error', 'detail': 'full_time + part_time != total'})
                for stem in ('applicants', 'admitted', 'enrolled'):
                    breakdown = [rec[f'{stem}_{suffix}'] for suffix in
                                 ('men', 'women', 'another_gender', 'gender_unknown')]
                    if rec[stem] and sum(int(x) for x in breakdown if x) > int(rec[stem]):
                        issues.append({'unitid': uid, 'year': year, 'rule': 'gender_subtotal',
                                       'severity': 'error', 'detail': f'{stem}: known breakdown exceeds total'})
                for score_count in ('sat_submit_count', 'act_submit_count'):
                    if rec[score_count] and rec['enrolled'] and int(rec[score_count]) > int(rec['enrolled']):
                        issues.append({'unitid': uid, 'year': year, 'rule': 'test_count',
                                       'severity': 'error', 'detail': f'{score_count} > enrolled'})
                for field in PCT_VARS.values():
                    if rec[field] and not (0 <= int(rec[field]) <= 100):
                        issues.append({'unitid': uid, 'year': year, 'rule': 'percent_range',
                                       'severity': 'error', 'detail': f'{field}={rec[field]}'})
                for stem, lo, hi in [('sat_reading', 200, 800), ('sat_math', 200, 800),
                                     ('sat_writing', 200, 800), ('act_composite', 1, 36),
                                     ('act_english', 1, 36), ('act_math', 1, 36), ('act_writing', 1, 36)]:
                    scores = [rec[f'{stem}_p{q}'] for q in ('25', '50', '75')]
                    for score in scores:
                        if score and not (lo <= int(score) <= hi):
                            issues.append({'unitid': uid, 'year': year, 'rule': 'score_range',
                                           'severity': 'error', 'detail': f'{stem}={score}'})
                    clean = [int(s) for s in scores if s]
                    if clean != sorted(clean):
                        issues.append({'unitid': uid, 'year': year, 'rule': 'score_percentiles',
                                       'severity': 'error', 'detail': f'{stem}={scores}'})
                panel.append(rec)
        yearly.append({'year': year, 'adm_rows': len(seen), 'matched_same_year_hd': matched_hd,
                       'unmatched_hd': len(seen) - matched_hd,
                       'complete_c1_triples': sum(1 for r in panel if r['cohort_year'] == str(year)
                                                  and r['applicants'] and r['admitted'] and r['enrolled'])})

    panel.sort(key=lambda r: (int(r['unitid']), int(r['cohort_year'])))
    metadata = ['unitid', 'cohort_year', 'institution_name', 'city', 'state', 'control_code',
                'control_label', 'sector_code', 'institution_level_code', 'locale_code',
            'carnegie_2000_code', 'carnegie_2005_basic_code',
            'carnegie_2015_basic_code', 'carnegie_2018_basic_code',
                'carnegie_2021_basic_code', 'carnegie_institutional_classification_code',
                'longitude', 'latitude']
    core = ['applicants', 'admitted', 'enrolled', 'admit_rate', 'yield_rate',
            'sat_submit_count', 'sat_submit_pct', 'act_submit_count', 'act_submit_pct',
            'sat_reading_p25', 'sat_reading_p50', 'sat_reading_p75',
            'sat_math_p25', 'sat_math_p50', 'sat_math_p75',
            'act_composite_p25', 'act_composite_p50', 'act_composite_p75',
            'test_policy_code', 'test_policy_label', 'test_policy_era',
            'test_policy_codebook_url', 'test_policy_codebook_sha256',
            'sat_reading_definition']
    used = set(metadata + core)
    extra = sorted(set(ADM_VARS.values()) - used)
    provenance = ['adm_release', 'adm_source_url', 'hd_source_url', 'has_matching_hd',
                  'ipeds_status_flags_json', 'special_value_codes_json']
    fields = metadata + core + extra + provenance
    write_csv(DATA / 'ipeds_admissions_panel.csv', panel, fields)

    group = defaultdict(list)
    for row in panel:
        group[row['unitid']].append(row)
    institutions = []
    for uid, rs in sorted(group.items(), key=lambda x: int(x[0])):
        best = next((r for r in reversed(rs) if r['has_matching_hd'] == '1'), rs[-1])
        institutions.append({'unitid': uid, 'institution_name': best['institution_name'],
                             'city': best['city'], 'state': best['state'],
                             'control_code': best['control_code'],
                             'control_label': best['control_label'],
                             'sector_code': best['sector_code'],
                             'institution_level_code': best['institution_level_code'],
                             'locale_code': best['locale_code'],
                             'carnegie_2000_code': best['carnegie_2000_code'],
                             'carnegie_2005_basic_code': best['carnegie_2005_basic_code'],
                             'carnegie_2015_basic_code': best['carnegie_2015_basic_code'],
                             'carnegie_2018_basic_code': best['carnegie_2018_basic_code'],
                             'carnegie_2021_basic_code': best['carnegie_2021_basic_code'],
                             'carnegie_institutional_classification_code': best['carnegie_institutional_classification_code'],
                             'longitude': best['longitude'], 'latitude': best['latitude'],
                             'metadata_year': best['cohort_year'],
                             'first_adm_year': rs[0]['cohort_year'],
                             'last_adm_year': rs[-1]['cohort_year'],
                             'adm_year_count': len(rs),
                             'adm_years': ';'.join(r['cohort_year'] for r in rs),
                             'metadata_source_url': best['hd_source_url']})
    write_csv(DATA / 'institutions.csv', institutions, list(institutions[0]))
    write_csv(VALIDATION / 'ipeds_v2_sources.csv', sources, list(sources[0]))
    write_csv(VALIDATION / 'ipeds_v2_year_coverage.csv', yearly, list(yearly[0]))
    write_csv(VALIDATION / 'ipeds_v2_issues.csv', issues,
              ['unitid', 'year', 'rule', 'severity', 'detail'])
    maps = []
    all_adm_columns = set().union(*map(set, adm_columns_by_year.values()))
    all_hd_columns = set().union(*map(set, hd_columns_by_year.values()))
    for raw, readable in ADM_VARS.items():
        years = [str(y) for y in range(2014, 2025) if raw in adm_columns_by_year[y]]
        maps.append({'component': 'ADM', 'original_variable': raw,
                     'readable_column': readable, 'years_present': ';'.join(years),
                     'unit': 'count' if raw in COUNT_VARS else 'percent_0_100' if raw in PCT_VARS
                     else 'score' if raw in SCORE_VARS else 'categorical_code',
                     'notes': ('Year-specific NCES valueSets codes and labels verified in '
                               'ipeds_v2_policy_codes.csv; semantic break begins in 2022.'
                               if raw == 'ADMCON7' else
                               'Negative NCES special values become blank and are preserved in special_value_codes_json.')})
    for raw, readable in HD_VARS.items():
        years = [str(y) for y in range(2014, 2025) if raw in hd_columns_by_year[y]]
        maps.append({'component': 'HD', 'original_variable': raw,
                     'readable_column': readable, 'years_present': ';'.join(years),
                     'unit': 'coordinate' if raw in ('LONGITUD', 'LATITUDE') else 'text_or_code',
                     'notes': 'Same-year HD joined on UNITID; institutions.csv uses latest matched HD year.'})
    for raw in sorted(all_adm_columns - set(ADM_VARS) - {'UNITID'}):
        if raw.startswith('X'):
            years = [str(y) for y in range(2014, 2025) if raw in adm_columns_by_year[y]]
            maps.append({'component': 'ADM', 'original_variable': raw,
                         'readable_column': 'ipeds_status_flags_json',
                         'years_present': ';'.join(years), 'unit': 'original_flag',
                         'notes': 'Stored as original NCES status flag key and value in JSON.'})
        else:
            raise ValueError(f'Unmapped ADM variable {raw}')
    write_csv(VALIDATION / 'ipeds_variable_mapping.csv', maps, list(maps[0]))
    summary = {'reporter_rows': len(panel), 'unique_institutions': len(institutions),
               'years': list(range(2014, 2025)), 'by_year': yearly,
               'matched_hd_rows': sum(int(r['matched_same_year_hd']) for r in yearly),
               'complete_c1_triples': sum(int(r['complete_c1_triples']) for r in yearly),
               'issues': dict(Counter(i['severity'] for i in issues)),
               'adm_raw_columns': len(all_adm_columns),
               'hd_selected_columns': len(HD_VARS),
               'source_tables': len(sources),
               'final_years': '2014-2023', 'provisional_years': '2024'}
    (VALIDATION / 'ipeds_v2_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if summary['issues'].get('error'):
        raise SystemExit(f"{summary['issues']['error']} IPEDS numeric issues; inspect ipeds_v2_issues.csv")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    build()
