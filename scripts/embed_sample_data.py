"""Embed the sample-data CSVs into the semantic model as compressed JSON.

Run after generate_sample_data.py:
    python scripts/embed_sample_data.py

Each Oracle-backed partition has a line of the form
    then LoadSampleData("<base64>", {type overrides})
and this script replaces the base64 payload with the current CSV contents
(header row + data rows, JSON, raw-deflate, base64), so the report refreshes
in sample mode with no file paths or credentials.
"""
import base64, csv, json, pathlib, re, zlib

repo = pathlib.Path(__file__).resolve().parent.parent
tables = repo / "ASX Quarterly Drilling Report.SemanticModel/definition/tables"
MAP = {
    "PPDM Extraction.tmdl": "ppdm_extraction.csv",
    "Well Status Statistics.tmdl": "well_status_statistics.csv",
    "Well Status Reference.tmdl": "well_status_reference.csv",
}
LINE = re.compile(r'then LoadSample(?:Csv|Data)\("[^"]*", (\{.*\})\)$', re.M)

for tmdl, csv_name in MAP.items():
    with open(repo / "sample-data" / csv_name, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    blob = co.compress(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()) + co.flush()
    payload = base64.b64encode(blob).decode()
    p = tables / tmdl
    text, n = LINE.subn(lambda m: f'then LoadSampleData("{payload}", {m.group(1)})', p.read_text(encoding="utf-8"))
    assert n == 1, f"{tmdl}: expected one LoadSampleData line, found {n}"
    p.write_text(text, encoding="utf-8")
    print(f"{tmdl}: {len(rows) - 1} rows, {len(payload) / 1024:.0f} KB embedded")
