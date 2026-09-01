#!/usr/bin/env python3
"""Parse saved EPA NLLAP and Michigan HTML into data/*.json."""
from __future__ import annotations

import html as htmllib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "sources"
DATA = ROOT / "data"

PHONE_RE = re.compile(r"\(\d{2,}\)\s*[\d\-]+(?:\s*(?:ext\.?|x)\s*\d+)?\s*$", re.I)
MULTI = sorted(
    [
        "Research Triangle Park",
        "North Chesterfield",
        "Long Island City",
        "Huntington Beach",
        "North Kansas City",
        "East Syracuse",
        "South Plainfield",
        "Rancho Cordova",
        "Jefferson City",
        "Oklahoma City",
        "Newport News",
        "Rocky Hill",
        "Carle Place",
        "Cherry Hill",
        "Baton Rouge",
        "New Hope",
        "San Diego",
        "New York",
        "St. Louis",
        "Saint Louis",
        "Mississauga, ON",
        "Nishihara Nakagami",
        "Long Beach",
    ],
    key=len,
    reverse=True,
)
ACCRED = {
    "1": "AIHA Laboratory Accreditation Programs",
    "2": "American Association for Laboratory Accreditation (A2LA)",
    "3": "Perry Johnson Laboratory Accreditation",
    "4": "ANSI-ASQ National Accreditation Board / ACLASS",
    "5": "International Accreditation Service",
}
STATE_NAME = {
    "AK": "Alaska", "AZ": "Arizona", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "IA": "Iowa", "IL": "Illinois", "IN": "Indiana",
    "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts", "MD": "Maryland",
    "ME": "Maine", "MI": "Michigan", "MN": "Minnesota", "MO": "Missouri",
    "NC": "North Carolina", "NJ": "New Jersey", "NY": "New York", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "PR": "Puerto Rico",
    "RI": "Rhode Island", "TN": "Tennessee", "TX": "Texas", "VA": "Virginia",
    "WA": "Washington", "WI": "Wisconsin", "ON/CA": "Ontario, Canada", "JPN": "Japan",
}


def txt(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    return " ".join(s.replace("\xa0", " ").split())


def table_cells(row: str) -> list[str]:
    return [txt(c) for c in re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", row, re.I)]


def split_company_city(raw: str) -> tuple[str, str, str]:
    m = PHONE_RE.search(raw)
    phone = m.group(0).strip() if m else ""
    rest = raw[: m.start()].strip() if m else raw
    rest = rest.rstrip(",").strip()
    rest2 = re.sub(r",\s*(LA|HI|CA|ON)\s*$", "", rest)
    for cityname in MULTI:
        if rest2.endswith(cityname):
            company = rest2[: -len(cityname)].strip().rstrip(",").strip()
            return company, cityname, phone
    parts = rest2.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1], phone
    return rest2, "", phone


def compile_nllap() -> None:
    html = (SRC / "epa-nllap.html").read_text(errors="replace")
    table = re.search(r"<table[\s\S]*?</table>", html, re.I).group(0)
    labs = []
    for r in re.findall(r"<tr[\s\S]*?</tr>", table, re.I):
        c = table_cells(r)
        if len(c) != 8 or c[0] == "State or Country":
            continue
        company, city, phone = split_company_city(c[2])
        labs.append(
            {
                "state": c[0],
                "state_name": STATE_NAME.get(c[0], c[0]),
                "accred_code": c[1],
                "accred": ACCRED.get(c[1], c[1]),
                "company": company,
                "city": city,
                "phone": phone,
                "as_printed": c[2],
                "lab_type": c[3],
                "commercial": "Yes" if c[4].lower() == "yes" else ("No" if c[4].lower() == "no" else ""),
                "paint": c[5] == "X",
                "soil": c[6] == "X",
                "dust": c[7] == "X",
            }
        )
    seen: dict = {}
    for i, lab in enumerate(labs):
        key = (lab["state"], lab["as_printed"])
        if key in seen:
            lab["duplicate_of_row"] = seen[key] + 1
            labs[seen[key]]["duplicated_later"] = True
        else:
            seen[key] = i
            lab["duplicate_of_row"] = None
    unique_n = sum(1 for lab in labs if lab["duplicate_of_row"] is None)
    meta = {
        "source": "https://www.epa.gov/lead/national-lead-laboratory-accreditation-program-list",
        "source_title": "National Lead Laboratory Accreditation Program List",
        "epa_round": "Round 131, Month 1 of 3 (July 2026)",
        "epa_updated": "2026-08-04",
        "retrieved": "2026-09-01",
        "rows": len(labs),
        "unique_labs": unique_n,
        "duplicate_rows": len(labs) - unique_n,
        "commercial_yes": sum(1 for l in labs if l["commercial"] == "Yes"),
        "commercial_no": sum(1 for l in labs if l["commercial"] == "No"),
        "paint": sum(1 for l in labs if l["paint"]),
        "soil": sum(1 for l in labs if l["soil"]),
        "dust": sum(1 for l in labs if l["dust"]),
        "states": dict(Counter(l["state"] for l in labs)),
    }
    (DATA / "nllap.json").write_text(json.dumps({"meta": meta, "labs": labs}, indent=2) + "\n")
    print(f"NLLAP {len(labs)} rows, {unique_n} unique")


def parse_mi(path: Path, role: str) -> list[dict]:
    html = path.read_text(errors="replace")
    people = []
    parts = re.split(r"(<h[23][^>]*>[\s\S]*?</h[23]>)", html, flags=re.I)
    county = ""
    skip = {"Popular on michigan.gov", "How Do I..."}
    for p in parts:
        hm = re.match(r"<h[23][^>]*>([\s\S]*?)</h[23]>", p, re.I)
        if hm:
            county = txt(hm.group(1))
            continue
        if county in skip:
            continue
        for table in re.findall(r"<table[\s\S]*?</table>", p, re.I):
            for r in re.findall(r"<tr[\s\S]*?</tr>", table, re.I):
                cells = table_cells(r)
                if not cells or cells[0] in ("Cert#", "Cert #") or "First Name" in cells:
                    continue
                if len(cells) < 7:
                    raise SystemExit(f"short MI row {role} {county} {cells}")
                people.append(
                    {
                        "cert": cells[0],
                        "first": cells[1],
                        "last": cells[2],
                        "suffix": cells[3],
                        "name": " ".join(x for x in [cells[1], cells[2], cells[3]] if x).strip(),
                        "firm": cells[4],
                        "city": cells[5],
                        "phone": "" if cells[6].lower() in ("not listed", "n/a", "") else cells[6],
                        "phone_as_printed": cells[6],
                        "county": county,
                        "role": role,
                    }
                )
    return people


def compile_michigan() -> None:
    insp = parse_mi(SRC / "mi-inspectors.html", "inspector")
    dual = parse_mi(SRC / "mi-inspector-risk-assessors.html", "inspector/risk assessor")
    people = insp + dual
    meta = {
        "source_hire": "https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional",
        "source_inspectors": "https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional/certified-lead-inspectors",
        "source_dual": "https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional/certified-lead-inspector-risk-assessors",
        "list_updated": "2026-08-27",
        "retrieved": "2026-09-01",
        "inspectors_only": len(insp),
        "inspector_risk_assessors": len(dual),
        "total": len(people),
    }
    (DATA / "michigan.json").write_text(json.dumps({"meta": meta, "people": people}, indent=2) + "\n")
    print(f"Michigan {len(insp)} inspectors, {len(dual)} dual, {len(people)} total")


if __name__ == "__main__":
    compile_nllap()
    compile_michigan()
