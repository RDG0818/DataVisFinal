"""Extract ADMCON7 value labels from all eleven official NCES Access workbooks."""
from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOKS = ROOT / 'raw/ipeds_v2/codebooks'
OUT = ROOT / 'validation'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def extract(path: Path, year: int):
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheets = workbook.findall('.//' + NS + 'sheet')
        valueset_sheet = next((x for x in sheets if x.get('name', '').lower().startswith('valuesets')), None)
        if valueset_sheet is None:
            raise ValueError(f'No valueSets sheet: {path}')
        relationship_id = valueset_sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        rel = next(x for x in relationships if x.get('Id') == relationship_id)
        sheet_path = 'xl/' + rel.get('Target').lstrip('/')
        sheet_path = sheet_path.replace('xl/xl/', 'xl/')
        shared_root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        shared = [''.join(t.text or '' for t in si.iter(NS + 't'))
                  for si in shared_root.findall(NS + 'si')]
        root = ET.fromstring(archive.read(sheet_path))
        result = []
        for row in root.findall('.//' + NS + 'sheetData/' + NS + 'row'):
            cells = {}
            for c in row.findall(NS + 'c'):
                raw = c.find(NS + 'v')
                val = raw.text if raw is not None else ''
                if c.get('t') == 's' and val:
                    val = shared[int(val)]
                ref = c.get('r', '')
                col = ref.rstrip('0123456789')
                cells[col] = val
            if cells.get('C', '').upper() == f'ADM{year}' and cells.get('F') == 'ADMCON7':
                result.append({'year': year, 'code': cells.get('G', ''),
                               'label': cells.get('K', ''),
                               'frequency': cells.get('H', ''),
                               'sheet': valueset_sheet.get('name'), 'sheet_row': row.get('r')})
        if not result:
            raise ValueError(f'ADMCON7 missing from {path}')
        return result


def main():
    acquisitions = {}
    for manifest in (BOOKS / 'codebook_acquisition_v1.json',
                     BOOKS / 'codebook_acquisition.json'):
        for row in json.loads(manifest.read_text()):
            if row.get('status') == 'downloaded':
                acquisitions[int(row['cohort_year'])] = row
    all_rows = []
    sources = []
    for year in range(2014, 2025):
        record = acquisitions[year]
        path = BOOKS / record['local_file']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != record['sha256']:
            raise ValueError(f'{year} codebook SHA256 mismatch')
        values = extract(path, year)
        for val in values:
            val['source_url'] = record['url']
            val['source_sha256'] = actual
            val['source_file'] = str(path.relative_to(ROOT))
        all_rows.extend(values)
        sources.append({'year': year, 'source_url': record['url'],
                        'sha256': actual, 'local_path': str(path.relative_to(ROOT)),
                        'ADMCON7_codes': ';'.join(x['code'] for x in values)})
    fields = ['year', 'code', 'label', 'frequency', 'sheet', 'sheet_row',
              'source_url', 'source_sha256', 'source_file']
    with (OUT / 'ipeds_v2_policy_codes.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(all_rows)
    with (OUT / 'ipeds_v2_codebook_sources.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, list(sources[0])); w.writeheader(); w.writerows(sources)
    print(json.dumps({'years': len(sources), 'ADMCON7_value_rows': len(all_rows),
                      'values_by_year': {str(year): {r['code']: r['label'] for r in all_rows
                                                    if r['year'] == year}
                                         for year in range(2014, 2025)}}, indent=2))


if __name__ == '__main__':
    main()
