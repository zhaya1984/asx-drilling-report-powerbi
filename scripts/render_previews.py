"""Render preview PNGs of key report pages from the synthetic sample data.

These are HTML re-creations of the Power BI page layouts (positions taken from the
PBIR visual.json files), not Power BI screenshots.
"""
import csv, html, pathlib, sys
from collections import Counter
from playwright.sync_api import sync_playwright

repo = pathlib.Path(sys.argv[1]); out = repo / "docs/images"; out.mkdir(parents=True, exist_ok=True)
ext = list(csv.DictReader(open(repo / "sample-data/ppdm_extraction.csv", encoding="utf-8")))
stat = list(csv.DictReader(open(repo / "sample-data/well_status_statistics.csv", encoding="utf-8")))
ref = list(csv.DictReader(open(repo / "sample-data/well_status_reference.csv", encoding="utf-8")))
e = html.escape

def fmt_date(s):
    if not s: return ""
    y, m, d = s.split("-"); return f"{int(d)}/{m}/{y[2:]}"
def quarters(r):
    return {r[k] for k in ("Spud Quarter Label", "Rig Release Quarter", "Child Spud Quarter", "Child Rig Release Quarter Label") if r[k]}

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1280px;height:720px;background:#fff;font-family:Inter,'DejaVu Sans',sans-serif;color:#252423;position:relative;overflow:hidden}
.v{position:absolute;overflow:hidden}
.title{font-size:13px;font-weight:600;padding:6px 8px 4px;color:#252423}
.hdr h1{font-size:22px;font-weight:700;color:#1f3b57;margin:10px 14px 6px}
.hdr p{font-size:11.5px;line-height:1.5;margin:0 14px;color:#444}
.hdr b{color:#1f3b57}
table{border-collapse:collapse;width:100%;font-size:11px}
th{text-align:left;font-weight:600;padding:5px 6px;border-bottom:1px solid #9a9a9a;white-space:nowrap;background:#fff;position:sticky;top:0}
td{padding:4px 6px;border-bottom:1px solid #eee;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px}
tr.sel td{background:#dbe9f7}
.tiles{display:flex;flex-wrap:wrap;gap:6px;padding:4px 8px}
.tile{border:1px solid #c8c6c4;border-radius:4px;font-size:11.5px;padding:7px 12px;background:#fff;min-width:70px;text-align:center}
.tile.on{background:#118dff;color:#fff;border-color:#118dff}
.col .tile{width:100%;text-align:left}
.sm{gap:4px}.sm .tile{min-width:0;padding:6px 8px;font-size:11px}
.dd{margin:4px 8px;border:1px solid #c8c6c4;font-size:12px;padding:6px 8px;display:flex;justify-content:space-between}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:10.5px}
.ok{background:#e3f4e8;color:#1e6b34}.bad{background:#fbe5e5;color:#9b1c1c}.drl{background:#fff4d6;color:#7a5600}.oth{background:#eef0f3;color:#3b4a5a}
.frame{border:1px solid #e1dfdd}
.badge{position:absolute;right:10px;bottom:6px;font-size:10px;color:#8a8886}
"""
def pill(s):
    c = "ok" if "Successful" in s and "Un" not in s else "bad" if "Unsuccessful" in s else "drl" if s == "Drilling" else "oth"
    return f'<span class="pill {c}">{e(s)}</span>'
def table(cols, rows, sel=None, render=None):
    h = "".join(f"<th>{e(c)}</th>" for c in cols)
    b = ""
    for i, r in enumerate(rows):
        cells = "".join(f"<td>{(render or {}).get(c, lambda v: e(v))(r.get(c, ''))}</td>" for c in cols)
        b += f'<tr class="{"sel" if sel == i else ""}">{cells}</tr>'
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"
def box(x, y, w, h, inner, cls=""): return f'<div class="v {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{inner}</div>'
def page(body): return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}<div class='badge'>Synthetic sample data</div></body></html>"

pages = {}

# ---------- Dynamic Report (Quarter = Q3 2026) ----------
Q = "Q3 2026"
rows = sorted([r for r in ext if Q in quarters(r)], key=lambda r: (int(r["Combined Sort"]), r["WELL NAME"]))
sel_i = next(i for i, r in enumerate(rows) if r["DW/ST WELL"]) if any(r["DW/ST WELL"] for r in rows) else 0
sel = dict(rows[sel_i])
desc = {s["WELL_NAME"]: s["STATUS_DESCRIPTION"] for s in stat}
sel["STATUS_DESCRIPTION"] = desc.get(sel["WELL NAME"], "")
for k in ("Spud Date", "Rig Release Date", "Child Spud Date", "Child Rig Release Date"): sel[k] = fmt_date(sel[k])
body = box(0, 0, 1279, 142, "<h1>ASX Drilling Dynamic Report</h1><p>Select the required quarter from the <b>Quarter</b> filter to generate the report. "
           "A well appears in every quarter in which it was spudded or reached rig release, including its latest sidetrack/deepen.</p>"
           "<p>The Well Status reflects the <b>current</b> well status and is not a historical snapshot.</p>", "hdr")
prods = sorted({r["Product Type"] for r in ext})
body += box(0, 164, 1059, 103, '<div class="title">Product Type</div><div class="tiles">' + "".join(f'<div class="tile">{p}</div>' for p in prods) + "</div>")
body += box(1058, 164, 221, 104, f'<div class="title">Quarter</div><div class="dd"><span>{Q}</span><span>▾</span></div>')
body += box(0, 268, 1059, 298, '<div class="title">ASX Summary</div>' + table(["WELL NAME", "STATE", "WORKING INTEREST", "STATUS"], rows, sel_i, {"STATUS": pill}), "frame")
body += box(1058, 267, 222, 84, '<div class="title">Current Class</div><div class="tiles sm">' + "".join(f'<div class="tile">{c}</div>' for c in ["EXP/APP", "DEV", "WATER"]) + "</div>")
body += box(1057, 351, 222, 369, '<div class="title">Basin</div><div class="tiles col">' + "".join(f'<div class="tile">{b}</div>' for b in sorted({r["Basin"] for r in ext})) + "</div>")
body += box(0, 564, 1058, 158, '<div class="title">Well Details</div>' + table(
    ["WELL NAME", "DW/ST WELL", "Current Class", "Basin", "Product Type", "Spud Date", "Rig Release Date", "Child Spud Date", "Child Rig Release Date", "PPDM Status", "STATUS_DESCRIPTION"], [sel]), "frame")
pages["dynamic-report"] = page(body)

# ---------- Current Quarter (Previous Quarter = Q3 2026) ----------
rows = sorted([r for r in ext if Q in quarters(r)], key=lambda r: (int(r["Combined Sort"]), r["WELL NAME"]))
body = box(0, 18, 1253, 125, "<h1>ASX Drilling Report — Current / Previous Quarter</h1><p>Built to match the published ASX report format. "
           "Use <b>… → Export data</b> on the table to paste straight into the quarterly report template.</p>"
           "<p>Sort order follows the ASX report: <b>Current Class → Basin → Product Type</b>.</p>", "hdr")
body += box(0, 143, 1280, 54, '<div class="tiles">' + "".join(f'<div class="tile{" on" if f == "Previous Quarter" else ""}">{f}</div>' for f in ["Earlier", "Previous Quarter", "Current Quarter"]) + "</div>")
cq = [dict(r, **{"Remarks": r["2nd Class"]}) for r in rows]
body += box(0, 197, 1280, 524, table(["Basin", "Product Type", "Current Class", "WELL NAME", "STATE", "WORKING INTEREST", "STATUS", "Remarks", "Reporting Spud Quarter", "Sidetrack/Deepen Well Spud Summary"],
                                    cq, None, {"STATUS": pill}), "frame")
pages["current-quarter"] = page(body)

# ---------- Well Status Observation ----------
reflk = {(r["STATUS_TYPE"], r["STATUS"]): r for r in ref}
missing = Counter((s["STATUS_TYPE"], s["CURRENT_STATUS"], s["ACTIVE_IND"]) for s in stat if s["CURRENT_STATUS"] in ("UNK", "") or not s["STATUS_TYPE"])
miss_rows = [{"STATUS_TYPE": k[0] or "(blank)", "CURRENT_STATUS": k[1] or "(blank)", "Count of WELL_NAME": str(v), "ACTIVE_IND": k[2] or "(blank)"} for k, v in missing.most_common()]
dist = Counter((s["STATUS_TYPE"], s["CURRENT_STATUS"]) for s in stat if s["STATUS_TYPE"])
dist_rows = [{"STATUS TYPE": k[0], "CURRENT STATUS": k[1], "LONG NAME": reflk.get(k, {}).get("LONG_NAME", ""), "Count of WELLs": str(v),
              "ACTIVE IND": reflk.get(k, {}).get("ACTIVE_IND", "")} for k, v in sorted(dist.items(), key=lambda kv: -kv[1])]
flag = lambda v: f'<span class="pill bad">{v}</span>' if v in ("N", "(blank)", "UNK") else e(v)
wd = sorted([s for s in stat if s["CURRENT_STATUS"] in ("UNK", "") or s["ACTIVE_IND"] == "N" or not s["STATUS_TYPE"]], key=lambda s: s["SPUD_DATE"], reverse=True)
wd = [dict(s, SPUD_DATE=fmt_date(s["SPUD_DATE"]), CURRENT_STATUS=s["CURRENT_STATUS"] or "(blank)", ACTIVE_IND=s["ACTIVE_IND"] or "(blank)") for s in wd]
body = box(0, 16, 1270, 134, "<h1>Well Status Observation</h1><p>Highlights wells with missing status information (blank <b>STATUS_TYPE</b> or a <b>CURRENT_STATUS</b> "
           "that is unknown or retired) against the full well status reference and distribution.</p><p>Click any row on the left to view the corresponding wells on the right. Scope: Australia and PNG wells.</p>", "hdr")
body += box(0, 160, 639, 136, '<div class="title">Status Type or Status Missing</div>' + table(["STATUS_TYPE", "CURRENT_STATUS", "Count of WELL_NAME", "ACTIVE_IND"], miss_rows, None,
                                                                                            {"STATUS_TYPE": flag, "CURRENT_STATUS": flag, "ACTIVE_IND": flag}), "frame")
body += box(0, 297, 639, 423, '<div class="title">Status Type Distribution</div>' + table(["STATUS TYPE", "CURRENT STATUS", "LONG NAME", "Count of WELLs", "ACTIVE IND"], dist_rows, None, {"ACTIVE IND": flag}), "frame")
body += box(639, 160, 641, 120, '<div class="title">Spud Date</div><div class="dd"><span>1/01/1985</span><span>8/10/2026</span></div>'
            '<div style="margin:14px 16px;height:4px;background:#118dff;border-radius:2px;position:relative"><span style="position:absolute;left:-6px;top:-5px;width:14px;height:14px;border-radius:50%;background:#fff;border:2px solid #118dff"></span><span style="position:absolute;right:-6px;top:-5px;width:14px;height:14px;border-radius:50%;background:#fff;border:2px solid #118dff"></span></div>')
body += box(638, 280, 641, 440, '<div class="title">Well Data</div>' + table(["WELL_NAME", "CURRENT_STATUS", "ACTIVE_IND", "SPUD_DATE", "PRIMARY_SOURCE"], wd, None,
                                                                            {"CURRENT_STATUS": flag, "ACTIVE_IND": flag}), "frame")
pages["well-status-observation"] = page(body)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
    for name, h in pages.items():
        pg.set_content(h); pg.wait_for_timeout(150)
        pg.screenshot(path=str(out / f"{name}.png"))
        print("wrote", name)
    b.close()
