"""Generate synthetic, fictional PPDM-shaped sample data for the ASX drilling report.

Reproduces the output contract of the three Oracle queries in the semantic model,
applying the same business rules as the SQL (sidetrack roll-up, status grouping,
quarter labels, combined sort, working-interest mapping).
"""
import csv, datetime as dt, pathlib, random, sys, uuid

OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(20261008)
TODAY = dt.date(2026, 10, 8)

# ---------------- reference: well status ----------------
WELL_STATUS = [  # code, long name, active, group
    ("SUG", "Suspended Gas Well", "Y", "C&S"), ("SUGO", "Suspended Gas & Oil Well", "Y", "C&S"),
    ("SUOG", "Suspended Oil & Gas Well", "Y", "C&S"), ("SUO", "Suspended Oil Well", "Y", "C&S"),
    ("SUGI", "Suspended Gas Injector", "Y", "C&S"), ("SFD", "Suspended for Future Development", "Y", "C&S"),
    ("CS", "Cased and Suspended", "Y", "C&S"), ("SST", "Suspended Stratigraphic Test", "N", "C&S"),
    ("PSG", "Plugged & Suspended Gas", "Y", "P&S"), ("PSO", "Plugged & Suspended Oil", "Y", "P&S"),
    ("SCG", "Successful Completed Gas", "Y", "C&C"), ("SCGC", "Successful Completed Gas Condensate", "Y", "C&C"),
    ("SCGO", "Successful Completed Gas & Oil", "Y", "C&C"), ("SCO", "Successful Completed Oil", "Y", "C&C"),
    ("SCW", "Successful Completed Water", "Y", "C&C"),
    ("ABOS", "Abandoned Oil Show", "Y", "P&A"), ("ABGO", "Abandoned Gas & Oil Show", "Y", "P&A"),
    ("ABGS", "Abandoned Gas Show", "Y", "P&A"), ("ABS", "Abandoned Dry", "Y", "P&A"),
    ("AST", "Abandoned Stratigraphic", "N", "P&A"), ("ABJ", "Abandoned Junked", "Y", "P&A"),
    ("PA", "Plugged and Abandoned", "Y", "P&A"), ("PAG", "Plugged and Abandoned Gas", "Y", "P&A"),
    ("PAO", "Plugged and Abandoned Oil", "Y", "P&A"), ("ABDH", "Abandoned Dry Hole", "N", "P&A"),
    ("OB", "Observation Well", "Y", "OBS"), ("DRI", "Drilling", "Y", "DRL"),
    ("STR", "Straddle Well", "Y", "OTH"), ("DOP", "Disposal Well", "Y", "OTH"),
    ("UNK", "Unknown", "N", "OTH"),
]
ONLINE_STATUS = [("ONL", "Online", "Y", "PROD"), ("OFFL", "Offline", "Y", "PROD"), ("SHUT", "Shut In", "Y", "PROD"),
                 ("PLND", "Planned", "N", "PLAN")]

GROUPS = {"C&S, Successful": ["SUG", "SUGO", "SUOG", "SUO", "SUGI", "SFD", "CS", "SST"],
          "P&S, Successful": ["PSG", "PSO"],
          "C&C, Successful": ["SCG", "SCGC", "SCGO", "SCO", "SCW"],
          "P&A, Unsuccessful": ["ABOS", "ABGO", "ABGS", "ABS", "AST", "ABJ", "PA", "PAG", "PAO", "ABDH"],
          "Observation Well": ["OB"], "Drilling": ["DRI"]}
CODE2GROUP = {c: g for g, cs in GROUPS.items() for c in cs}
LONG = {c: n for c, n, *_ in WELL_STATUS + ONLINE_STATUS}

def d(x): return x.isoformat() if x else ""

ref_rows = []
for stype, rows in (("WELL_STATUS", WELL_STATUS), ("ONLINE_STATUS", ONLINE_STATUS)):
    for code, name, active, grp in rows:
        created = dt.date(2012, 3, 1) + dt.timedelta(days=rng.randint(0, 2500))
        changed = created + dt.timedelta(days=rng.randint(0, 3000)) if rng.random() < 0.55 else None
        if changed and changed > TODAY: changed = TODAY - dt.timedelta(days=rng.randint(30, 400))
        eff = created
        exp = (changed or created + dt.timedelta(days=1500)) if active == "N" else None
        ref_rows.append({
            "STATUS_TYPE": stype, "STATUS": code, "ABBREVIATION": code, "ACTIVE_IND": active,
            "EFFECTIVE_DATE": d(eff), "EXPIRY_DATE": d(exp), "LONG_NAME": name,
            "PPDM_GUID": str(uuid.UUID(int=rng.getrandbits(128))).upper(),
            "REMARK": ("Retired - superseded by standard code" if active == "N" else ""),
            "SHORT_NAME": name[:20], "SOURCE": rng.choice(["PPDM", "LEGACY_MIGRATION"]),
            "STATUS_GROUP": grp, "ROW_CHANGED_BY": "DATA_ADMIN" if changed else "",
            "ROW_CHANGED_DATE": d(changed), "ROW_CREATED_BY": rng.choice(["DATA_ADMIN", "MIGRATION_SVC"]),
            "ROW_CREATED_DATE": d(created), "ROW_QUALITY": "VALID", "PLOT_SYMBOL": "",
        })

# ---------------- geography / commercial set-up (all fictional) ----------------
BASINS = {  # basin: (states, env, products, jv contracts, permit prefix, country, class weights)
    "Basin A": (["SA", "QLD"], "ONSHORE", ["OIL", "GAS", "OG"], ["JV Alpha", "JV Bravo", "Permit Golf"], "PPL", "AU",
                {"DEV": 60, "EXP": 12, "APP": 12, "NFE": 6, "WTR": 4}),
    "Basin B": (["QLD"], "ONSHORE", ["CSG", "GAS"], ["JV Charlie", "JV Delta Unit"], "PL", "AU",
                {"DEV": 75, "APP": 10, "EXP": 5, "WTR": 6}),
    "Basin C": (["NSW"], "ONSHORE", ["CSG"], ["Permit Echo"], "PEL", "AU", {"DEV": 50, "APP": 30, "EXP": 20}),
    "Basin D": (["NT"], "OFFSHORE", ["GAS", "CDS"], ["Permit Foxtrot", "JV Hotel"], "NT/RL", "AU",
                {"DEV": 50, "APP": 30, "EXP": 20}),
    "Basin E": (["WESTERN"], "ONSHORE", ["GAS", "OIL"], ["JV Delta Unit", "Permit Foxtrot"], "PDL", "PG",
                {"DEV": 55, "EXP": 25, "APP": 20}),
    "Basin F": (["WA"], "OFFSHORE", ["OIL", "GAS"], ["Permit Echo", "JV India"], "WA-", "AU",
                {"DEV": 55, "EXP": 25, "APP": 20}),
    "Basin G": (["WA"], "OFFSHORE", ["OIL"], ["JV Bravo"], "WA-", "AU", {"EXP": 60, "APP": 40}),
}
BASIN_W = {"Basin A": 38, "Basin B": 34, "Basin C": 5, "Basin D": 6, "Basin E": 7, "Basin F": 6, "Basin G": 4}
INTEREST = {"JV Alpha": "60.00%", "JV Bravo": "75.00%", "JV Charlie": "30.00%", "JV Delta Unit": "50.00%",
            "Permit Echo": "100.00%", "Permit Foxtrot": "25.00%", "Permit Golf": "42.50%"}  # Hotel / India unmapped -> NULL
BASIN_ORD = {b: i + 1 for i, b in enumerate(BASINS)}
CLASS_ORD = {"EXP": 1, "APP": 1, "NFE": 1, "DEV": 4, "WTR": 5}
PROD_ORD = {"OIL": 1, "GAS": 2, "OG": 3, "CSG": 4, "CDS": 5, "WTR": 6, "COAL": 7}
SECOND = {"DEV": ["Infill", "Step-out", "Re-entry", ""], "EXP": ["Wildcat", "Near-field", ""],
          "APP": ["Appraisal", "Extended appraisal", ""], "NFE": ["Near-field", ""], "WTR": ["Water supply", "Monitoring"]}

SYL = ["ka", "ran", "do", "mi", "lu", "ta", "bo", "ren", "wi", "nal", "go", "ri", "ma", "tor", "ya", "lin", "ba", "der",
       "nu", "ko", "ral", "pe", "sin", "ga", "mo", "dar", "ti", "wen"]
def field_name():
    return ("".join(rng.choice(SYL) for _ in range(rng.choice([2, 3])))).upper()
FIELDS = {b: list({field_name() for _ in range(9)}) for b in BASINS}

def wpick(dct): return rng.choices(list(dct), weights=list(dct.values()))[0]
def qlabel(x): return f"Q{(x.month - 1) // 3 + 1} {x.year}" if x else ""
def qstart(x): return dt.date(x.year, 3 * ((x.month - 1) // 3) + 1, 1)
def rand_date(a, b): return a + dt.timedelta(days=rng.randint(0, (b - a).days))

# ---------------- wells ----------------
field_counter = {}
def next_name(basin):
    f = rng.choice(FIELDS[basin])
    field_counter[f] = field_counter.get(f, 0) + 1 + (rng.random() < 0.2)
    return f"{f}-{field_counter[f]}"

def final_status(cls, env, spud, rr, product):
    if rr is None: return "DRI"
    if cls == "WTR": return rng.choice(["SCW", "OB"])
    r = rng.random()
    if cls == "DEV":
        if r < 0.70: return {"OIL": "SCO", "GAS": "SCG", "OG": "SCGO", "CSG": "SCG", "CDS": "SCGC"}[product]
        if r < 0.85: return rng.choice(["SUG", "SUO", "CS", "SFD"])
        return rng.choice(["PA", "ABJ", "PAG"])
    if r < 0.30: return rng.choice(["SUG", "SUGO", "SUO", "CS", "SFD"])
    if r < 0.42: return rng.choice(["PSG", "PSO"])
    if r < 0.50: return rng.choice(["SCG", "SCO"])
    return rng.choice(["ABOS", "ABGS", "ABS", "PA", "PAO", "ABGO"])

wells = []  # every WELL row (parents, children, out-of-scope)
uwi_n = 100000
def new_uwi():
    global uwi_n; uwi_n += rng.randint(1, 40); return f"AU{uwi_n:08d}"

START, END = dt.date(2020, 1, 2), TODAY
quarters_spud = []
for _ in range(185):
    basin = rng.choices(list(BASIN_W), weights=list(BASIN_W.values()))[0]
    states, env, prods, jvs, pprefix, country, clsw = BASINS[basin]
    cls = wpick(clsw); product = "WTR" if cls == "WTR" else rng.choice(prods)
    spud = rand_date(START, END)
    dur = rng.randint(4, 14) if env == "ONSHORE" and product == "CSG" else rng.randint(9, 35) if env == "ONSHORE" else rng.randint(25, 70)
    rr = spud + dt.timedelta(days=dur)
    if rr > TODAY: rr = None
    status = final_status(cls, env, spud, rr, product)
    jv = rng.choice(jvs)
    wells.append(dict(UWI=new_uwi(), WELL_NAME=next_name(basin), basin=basin, STATE=rng.choice(states), env=env,
                      COUNTRY=country, cls=cls, product=product, spud=spud, rr=rr, status=status, jv=jv,
                      permit=f"{pprefix} {rng.randint(10, 399)}" if not pprefix.endswith("-") else f"{pprefix}{rng.randint(10, 79)}-L",
                      second=rng.choice(SECOND[cls]), parent=None,
                      op="COMPANY" if rng.random() < 0.88 else "PARTNER ENERGY", in_scope=True))

# make sure the current and previous quarter are well populated
for target_q_start, n in ((dt.date(2026, 7, 1), 9), (dt.date(2026, 10, 1), 3)):
    for w in rng.sample([w for w in wells if w["basin"] in ("Basin A", "Basin B")], n):
        w["spud"] = rand_date(target_q_start, min(target_q_start + dt.timedelta(days=88), TODAY - dt.timedelta(days=1)))
        rr = w["spud"] + dt.timedelta(days=rng.randint(5, 30))
        w["rr"] = rr if rr <= TODAY else None
        w["status"] = final_status(w["cls"], w["env"], w["spud"], w["rr"], w["product"])

# sidetracks / deepens
children = []
for w in rng.sample([w for w in wells if w["rr"] and w["cls"] != "WTR"], 22):
    k = rng.choice([1, 1, 1, 2])
    last = w["rr"]
    for i in range(1, k + 1):
        cs = last + dt.timedelta(days=rng.randint(3, 500))
        if cs > TODAY: break
        crr = cs + dt.timedelta(days=rng.randint(6, 30))
        crr = crr if crr <= TODAY else None
        kind = "ST" if rng.random() < 0.8 else "DW"
        c = dict(w, UWI=new_uwi(), WELL_NAME=f"{w['WELL_NAME']} {kind}{i}", spud=cs, rr=crr,
                 status=final_status(w["cls"], w["env"], cs, crr, w["product"]), parent=w["UWI"], in_scope=False)
        children.append(c); last = crr or cs
# two children with a missing spud date (excluded from latest-child logic)
for w in rng.sample([w for w in wells if w["rr"]], 2):
    children.append(dict(w, UWI=new_uwi(), WELL_NAME=f"{w['WELL_NAME']} ST9", spud=None, rr=None, status="UNK",
                         parent=w["UWI"], in_scope=False))

# out-of-scope wells (straddle/disposal, pre-2020, other BU) — appear only in Well Status Statistics
others = []
for _ in range(70):
    basin = rng.choice(list(BASINS)); states, env, prods, *_ = BASINS[basin]
    spud = rand_date(dt.date(1985, 1, 1), dt.date(2019, 12, 31))
    others.append(dict(UWI=new_uwi(), WELL_NAME=next_name(basin), STATE=rng.choice(states), COUNTRY=BASINS[basin][5],
                       spud=spud, status=rng.choice(["SCG", "SCO", "PA", "SUG", "CS", "ABS", "ONL", "SHUT", "OFFL"])))
for s in ["STR", "STR", "DOP", "DOP", "DOP"]:
    w = rng.choice(wells); others.append(dict(UWI=new_uwi(), WELL_NAME=next_name(w["basin"]), STATE=w["STATE"],
                                              COUNTRY=w["COUNTRY"], spud=rand_date(START, END), status=s))
# data-quality cases for the Well Status Observation page
for s in ["UNK", "UNK", "UNK", None, None, "SST", "AST", "ABDH", "ABDH"]:
    basin = rng.choice(list(BASINS))
    others.append(dict(UWI=new_uwi(), WELL_NAME=next_name(basin), STATE=rng.choice(BASINS[basin][0]),
                       COUNTRY=BASINS[basin][5], spud=rand_date(dt.date(1995, 1, 1), dt.date(2023, 1, 1)), status=s,
                       missing_type=(s is None)))

# ---------------- PPDM Extraction (applies the SQL rules) ----------------
by_parent = {}
for c in children:
    if c["spud"] and c["spud"] > dt.date(1900, 1, 1):
        by_parent.setdefault(c["parent"], []).append(c)

ext_rows = []
for w in wells:
    if w["status"] in ("STR", "DOP") or w["spud"] <= dt.date(2020, 1, 1):
        continue
    ls = max(by_parent.get(w["UWI"], []), key=lambda c: c["spud"], default=None)
    eff = ls["status"] if ls else w["status"]
    combined = CLASS_ORD.get(w["cls"], 99) * 10000 + BASIN_ORD.get(w["basin"], 99) * 100 + PROD_ORD.get(w["product"], 99)
    summary = (f"Original well spud at {qlabel(w['spud'])}, {ls['WELL_NAME']} spud at {qlabel(ls['spud'])}" if ls else "")
    ext_rows.append({
        "WELL NAME": w["WELL_NAME"], "DW/ST WELL": ls["WELL_NAME"] if ls else "", "STATE": w["STATE"],
        "Sidetrack/Deepen Well Spud Summary": summary, "WORKING INTEREST": INTEREST.get(w["jv"], ""),
        "STATUS": CODE2GROUP.get(eff, "-"), "PPDM Status": eff, "Asset Verification": "",
        "Product Type": w["product"], "Operated/Interest": "BU01", "Environment Type": w["env"],
        "Country": w["COUNTRY"], "Basin": w["basin"], "Initial Operator": w["op"], "Current Operator": w["op"],
        "Current JV": w["jv"], "Permit": w["permit"], "Current Class": w["cls"], "2nd Class": w["second"],
        "Well Category": {"EXP": "EXP/APP", "APP": "EXP/APP", "NFE": "EXP/APP", "DEV": "DEV", "WTR": "WATER"}.get(w["cls"], ""),
        "Spud Date": d(w["spud"]), "Rig Release Date": d(w["rr"]),
        "Child Spud Date": d(ls["spud"]) if ls else "", "Child Rig Release Date": d(ls["rr"]) if ls else "",
        "Latest ST Spud Quarter Sort": d(qstart(ls["spud"])) if ls else "", "Combined Sort": combined,
        "Spud Quarter Label": qlabel(w["spud"]), "Rig Release Quarter": qlabel(w["rr"]),
        "Child Spud Quarter": qlabel(ls["spud"]) if ls else "",
        "Child Rig Release Quarter Label": qlabel(ls["rr"]) if ls and ls["rr"] else "",
        "Reporting Spud Quarter": qlabel(ls["spud"] if ls else w["spud"]),
    })
ext_rows.sort(key=lambda r: (r["Combined Sort"], r["Spud Date"]))

# ---------------- Well Status Statistics ----------------
ref_lookup = {(r["STATUS_TYPE"], r["STATUS"]): r for r in ref_rows}
stat_rows = []
for w in wells + children + others:
    code = w["status"]
    stype = "" if w.get("missing_type") else ("ONLINE_STATUS" if code in {"ONL", "OFFL", "SHUT", "PLND"} else "WELL_STATUS")
    ref = ref_lookup.get((stype, code)) if code else None
    stat_rows.append({
        "COUNTRY": w["COUNTRY"], "STATUS_TYPE": stype, "CURRENT_STATUS": code or "",
        "STATUS_DESCRIPTION": (ref["LONG_NAME"] if ref else (code or "")),
        "ACTIVE_IND": ref["ACTIVE_IND"] if ref else "", "UWI": w["UWI"], "WELL_NAME": w["WELL_NAME"],
        "WELL_NUM": w["WELL_NAME"].split("-")[-1], "PRIMARY_SOURCE": rng.choice(["PPDM", "LEGACY_MIGRATION", "FIELD_ENTRY"]),
        "SPUD_DATE": d(w["spud"]),
    })

# ---------------- integrity checks (model relationships) ----------------
names = [r["WELL_NAME"] for r in stat_rows]
assert len(names) == len(set(names)), "WELL_NAME must be unique (1:1 relationship)"
assert len({r["WELL NAME"] for r in ext_rows}) == len(ext_rows)
assert set(r["WELL NAME"] for r in ext_rows) <= set(names)
assert len({r["STATUS"] for r in ref_rows}) == len(ref_rows), "STATUS must be unique (many-to-one target)"

def write(name, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
write("ppdm_extraction.csv", ext_rows)
write("well_status_statistics.csv", stat_rows)
write("well_status_reference.csv", ref_rows)
print(len(ext_rows), "report wells |", len(stat_rows), "status rows |", len(ref_rows), "reference rows |",
      sum(1 for r in ext_rows if r["DW/ST WELL"]), "with sidetrack")
