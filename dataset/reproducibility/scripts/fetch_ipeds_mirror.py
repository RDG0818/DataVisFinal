#!/usr/bin/env python3
"""Acquire small IPEDS ADM/HD mirror CSVs with explicit acquisition provenance.
NCES TLS failure means these files must never be described as direct NCES downloads.
"""
import csv, datetime, hashlib, json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"raw/ipeds"
OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for year in [2022,2023]:
    for table in ["ADM","HD"]:
        name=f"{table}{year}"
        source=f"https://nces.ed.gov/ipeds/datacenter/data/{name}.zip"
        retrieval=f"https://media.githubusercontent.com/media/ftrain/ipeds2/main/sources/IPEDS{year}{str(year+1)[2:]}_csv/{name}.csv"
        target=OUT/f"{name}_mirror.csv"
        if not target.exists():
            resp=requests.get(retrieval,timeout=30)
            resp.raise_for_status()
            if not resp.content.startswith(b"UNITID,"):raise ValueError("Unexpected CSV schema")
            target.write_bytes(resp.content)
        rows.append({"table":name,"cohort_year":year,"official_source_url":source,
            "retrieval_url":retrieval,"local_path":str(target.relative_to(ROOT)),
            "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
            "retrieved_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "acquisition":"third_party_Git_LFS_mirror_of_NCES_export",
            "direct_NCES_acquisition_verified":"false",
            "notes":"Direct NCES HTTPS failed SSL EOF. Mirror identifies NCES final/revised release; byte identity to official download not independently verified. Used solely as independent cross-check, never to fill CDS."})
        print(name,target.stat().st_size,flush=True)
with (ROOT/"validation/ipeds_sources.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
