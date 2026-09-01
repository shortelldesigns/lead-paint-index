#!/usr/bin/env python3
"""Generate Lead Paint Index static pages from transcribed official lists."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
labs_doc = json.loads((DATA / "nllap.json").read_text())
mi_doc = json.loads((DATA / "michigan.json").read_text())
LABS = labs_doc["labs"]
LAB_META = labs_doc["meta"]
PEOPLE = mi_doc["people"]
MI_META = mi_doc["meta"]

UNIQUE_LABS = [l for l in LABS if not l.get("duplicate_of_row")]
N_ROWS = LAB_META["rows"]
N_UNIQUE = LAB_META["unique_labs"]
N_INSP = MI_META["inspectors_only"]
N_DUAL = MI_META["inspector_risk_assessors"]
N_MI = MI_META["total"]

NAV = [
    ("index.html", "Home"),
    ("how-to.html", "How to test"),
    ("labs.html", "NLLAP labs"),
    ("michigan.html", "Michigan"),
    ("verify.html", "Verify a pro"),
    ("about.html", "About"),
]


def nav_html(current: str) -> str:
    bits = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        bits.append(f'<a href="{href}"{cur}>{label}</a>')
    return "\n        ".join(bits)


FOOT_NAV = " ".join(f'<a href="{h}">{lab}</a>' for h, lab in NAV)

FOOTER_BLURB = (
    "Lead Paint Index is an independent public directory compiled by Stephen Shortell. "
    "It is not a laboratory, not a lead contractor, and not Shortell Designs. "
    "It is not endorsed by the U.S. EPA, HUD, or any state lead program. "
    "Names are transcribed from official lists. Certification and accreditation change. "
    "Verify a current credential with the issuing agency before hiring. "
    "No paid placement on professional or laboratory lists. "
    "As an Amazon Associate I earn from qualifying purchases."
)


def page(title: str, desc: str, current: str, body: str, main_class: str = "") -> str:
    wrap = "wrap-prose prose" if main_class == "prose" else "wrap"
    inner = body if main_class == "prose" else f'<div class="{wrap}">\n{body}\n    </div>'
    if main_class == "prose":
        inner = f'<article class="wrap-prose prose">\n{body}\n    </article>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(desc)}">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="index.html">
        <span class="brand-mark" aria-hidden="true">Pb</span>
        <span class="brand-text">
          <span class="brand-name">Lead Paint Index</span>
          <span class="brand-sub">NLLAP labs · Michigan inspectors</span>
        </span>
      </a>
      <nav aria-label="Primary">
        {nav_html(current)}
      </nav>
    </div>
  </header>
  <main id="main">
    {inner}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p class="byline">Stephen Shortell</p>
      <p>{FOOTER_BLURB}</p>
      <p class="foot-nav">{FOOT_NAV}</p>
    </div>
  </footer>
</body>
</html>
"""


def matrices(lab: dict) -> str:
    bits = []
    if lab["paint"]:
        bits.append('<span class="svc svc-m">Paint</span>')
    if lab["soil"]:
        bits.append('<span class="svc svc-b">Soil</span>')
    if lab["dust"]:
        bits.append('<span class="svc svc-x">Dust</span>')
    return " ".join(bits) or "—"


def hay(*parts: str) -> str:
    return escape(" ".join(p for p in parts if p).lower())


def index_page() -> str:
    # state cards for top NLLAP states
    by_state: dict[str, int] = {}
    unique_by_state: dict[str, int] = {}
    name_of: dict[str, str] = {}
    for lab in LABS:
        by_state[lab["state"]] = by_state.get(lab["state"], 0) + 1
        name_of[lab["state"]] = lab["state_name"]
    for lab in UNIQUE_LABS:
        unique_by_state[lab["state"]] = unique_by_state.get(lab["state"], 0) + 1
    # keep US-ish states first, drop JPN/ON from homepage cards (still in labs.html)
    skip = {"JPN", "ON/CA"}
    ranked = sorted(
        ((k, unique_by_state.get(k, 0)) for k in unique_by_state if k not in skip),
        key=lambda kv: (-kv[1], kv[0]),
    )
    state_cards = []
    for code, n in ranked[:8]:
        state_cards.append(
            f"""        <a class="card" href="labs.html#st-{escape(code)}">
          <p class="kicker">{escape(name_of[code])}</p>
          <p class="stat">{n}<small>NLLAP lab{'s' if n != 1 else ''} (unique)</small></p>
          <p class="meta">EPA list updated 2026-08-04. Confirm current recognition before you ship a sample.</p>
        </a>"""
        )
    body = f"""
      <p class="kicker">Public directory</p>
      <h1>Find a certified lead inspector, or a recognized test kit</h1>
      <p class="lede">An independent index of EPA-recognized NLLAP laboratories and Michigan’s published certified lead inspectors and inspector/risk assessors. Names are transcribed from those sources. No invented labs. No paid placement.</p>

      <div class="paths">
        <p class="paths-label">Two ways to get an answer</p>
        <a class="path" href="labs.html">
          <strong>Hire a certified inspector or lab</strong>
          <span>{N_UNIQUE} unique NLLAP labs · {N_MI} Michigan certified people. No paid placement.</span>
        </a>
        <a class="path" href="how-to.html">
          <strong>Screen it yourself</strong>
          <span>EPA-recognized kits are a screen, not a full inspection.</span>
        </a>
      </div>

      <div class="grid states" id="counts">
        <a class="card" href="labs.html">
          <p class="kicker">National · NLLAP</p>
          <p class="stat">{N_UNIQUE}<small>unique EPA-recognized labs</small></p>
          <p>{N_ROWS} rows on the Round 131 table ({LAB_META['duplicate_rows']} duplicate rows as printed).</p>
          <p class="meta">Paint chips, dust wipes, and/or soil. Updated 2026-08-04. Retrieved 2026-09-01.</p>
        </a>
        <a class="card" href="michigan.html">
          <p class="kicker">Michigan · MDHHS MiLeadSafe</p>
          <p class="stat">{N_MI}<small>certified inspectors / risk assessors</small></p>
          <p>{N_INSP} inspector only · {N_DUAL} inspector/risk assessor.</p>
          <p class="meta">Official lists updated 2026-08-27. Retrieved 2026-09-01.</p>
        </a>
        <a class="card" href="verify.html">
          <p class="kicker">Other states</p>
          <p class="stat">EPA locator<small>search form, not a downloadable roster</small></p>
          <p>The federal firm locator is a JavaScript search. This index does not invent names to fill that gap.</p>
          <p class="meta">Use EPA’s locator, then verify the certificate.</p>
        </a>
        <a class="card card-howto" href="how-to.html">
          <p class="kicker">Do it yourself</p>
          <h2>How to test a home for lead paint</h2>
          <p>Pre-1978 housing, HUD/EPA disclosure, when a kit is only a screen, and when to hire a certified inspector or risk assessor.</p>
        </a>
      </div>

      <h2>NLLAP labs by state (largest counts)</h2>
      <div class="grid states">
{chr(10).join(state_cards)}
      </div>
      <p class="meta">Counts are unique laboratories after dropping three duplicate rows that EPA printed twice. The full table, including duplicates as published, is on the <a href="labs.html">NLLAP labs page</a>.</p>

      <h2>How to use these lists</h2>
      <ul class="plain">
        <li>A kit that turns color is a <strong>screen</strong>. EPA-recognized kits, when used by a trained professional, can support a negative finding that regulated lead-based paint is not present on certain surfaces. They are not a lead-based paint inspection or a risk assessment.</li>
        <li>A <strong>certified inspector</strong> tells you whether lead-based paint is present and where. A <strong>certified risk assessor</strong> tells you whether current hazards exist in paint, dust, or soil and what to do about them.</li>
        <li>Paint chips, dust wipes, and soil that need laboratory analysis should go to an <strong>NLLAP-recognized lab</strong> for the matrix you are sending.</li>
        <li>City is the address of record on the source list. Some Michigan certificate holders are based in another state.</li>
        <li>The EPA Lead-based Paint Professional Locator is a search form. This site does not scrape it. <a href="verify.html">Verify a professional</a> on EPA’s locator or a state list.</li>
      </ul>
"""
    return page(
        "Certified Lead Inspector or DIY Kit | Lead Paint Index",
        "Find EPA-recognized NLLAP lead labs and Michigan certified lead inspectors, or follow a DIY kit. Compiled by Stephen Shortell. Unpaid directory, not EPA-endorsed.",
        "index.html",
        body,
    )


def how_to_page() -> str:
    body = r"""
      <h1>How to test a home for lead-based paint</h1>
      <p>Most U.S. housing built before 1978 — “target housing” under federal lead rules — may contain lead-based paint. You cannot tell by looking. This page summarizes EPA and HUD consumer guidance. It is not medical, legal, or real-estate advice.</p>
      <p><strong>Federal definition of lead-based paint</strong> in housing is paint with lead equal to or greater than <strong>1.0 milligram per square centimeter (mg/cm²)</strong> or <strong>0.5% by weight</strong> (5,000 ppm). A color-change swab that looks “positive” is not the same thing as that measurement.</p>
      <p class="meta">Sources: <a href="https://www.epa.gov/lead/real-estate-disclosures-about-potential-lead-hazards">EPA, Real Estate Disclosures about Potential Lead Hazards</a>; <a href="https://www.epa.gov/lead/testkits">EPA, Lead Test Kits</a>. Retrieved 2026-09-01.</p>
      <hr>
      <h2>Pre-1978 housing and the HUD/EPA disclosure rule</h2>
      <p>The federal Lead-based Paint Disclosure Rule applies to most pre-1978 private, public, federally owned, and federally assisted housing. Before a buyer signs a contract or a renter signs a lease, sellers, landlords, real estate agents, and property managers must:</p>
      <ul>
        <li>Give the EPA/HUD pamphlet <cite>Protect Your Family From Lead in Your Home</cite>.</li>
        <li>Disclose known lead-based paint and lead-based paint hazards, and share available records and reports.</li>
        <li>Include a Lead Warning Statement in the contract or lease.</li>
        <li>Give homebuyers a 10-day opportunity to have a certified inspector or risk assessor check the housing (parties may agree in writing to a different period; buyers may waive it).</li>
      </ul>
      <p>The rule does not itself require the seller or landlord to test. It requires disclosure of <em>known</em> information. If you are buying pre-1978 housing and you care about lead, use the 10-day window — or negotiate a longer one — and hire a certified professional rather than relying on a hardware-store swab.</p>
      <p>Source: <a href="https://www.epa.gov/lead/real-estate-disclosures-about-potential-lead-hazards">Real Estate Disclosures about Potential Lead Hazards</a> (retrieved 2026-09-01). Pamphlet: <a href="https://www.epa.gov/system/files/documents/2026-02/protectyourfamily_pamphlet_2026_3.pdf">Protect Your Family From Lead in Your Home (PDF, 2026)</a>.</p>
      <hr>
      <h2>A kit is a screen, not a full inspection</h2>
      <p>EPA recognizes three lead test kits for use under the Renovation, Repair, and Painting (RRP) Rule: <strong>LeadCheck™</strong> (now made by Luxfer Magtech), <strong>D-Lead®</strong> (ESCA Tech), and a <strong>Commonwealth of Massachusetts</strong> kit. They meet the <em>negative-response</em> criterion only. EPA states that, to date, no kit has met both the negative- and positive-response criteria in 40 CFR 745.88(c).</p>
      <p>What that means in practice:</p>
      <ul>
        <li>EPA recognition applies when a <strong>trained professional</strong> (a certified renovator, inspector, or risk assessor) uses the kit on the surfaces EPA evaluated.</li>
        <li>LeadCheck™ and D-Lead® are recognized on wood, ferrous metal, drywall, and plaster. The Massachusetts kit is recognized on drywall and plaster only — not wood or ferrous metal.</li>
        <li>A negative result, used that way, can support a finding that regulated lead-based paint is <em>not</em> present on that tested surface. A positive result, a kit used on some other surface, or a homeowner swab is <strong>not</strong> a lead-based paint inspection.</li>
        <li>You may still assume lead is present in pre-1978 paint and follow lead-safe work practices without testing.</li>
      </ul>
      <p>Source: <a href="https://www.epa.gov/lead/testkits">EPA Lead Test Kits</a> (retrieved 2026-09-01).</p>
      <div class="note">
        <p>If you are buying or selling, documenting hazards for a child, or deciding whether to abate, hire a <a href="verify.html">certified inspector or risk assessor</a>. Do not treat a DIY swab as the 10-day inspection opportunity under the disclosure rule.</p>
      </div>
      <h3>1. EPA-recognized color-change kit (screen)</h3>
      <p>LeadCheck™ swabs are crushed, shaken, and rubbed on a painted surface. A pink or red color indicates lead. EPA’s recognition is for a <em>negative</em> finding by a trained professional on listed surfaces. Homeowner use is a screen only.</p>
      <h3>2. Mail-in sample to an NLLAP laboratory</h3>
      <p>A paint chip, dust wipe, or soil sample analyzed by an EPA-recognized NLLAP lab is a laboratory result for that sample, not a whole-house inspection. Schneider Laboratories, Inc. (Richmond, Virginia) appears on the NLLAP list retrieved 2026-09-01. Consumer mail-in kits sold under that lab’s name are <strong>not</strong> EPA-recognized RRP test kits. They are sample-collection kits whose analysis is done at a lab.</p>
      <h3>3. Certified inspector or risk assessor</h3>
      <p>A certified inspector uses X-ray fluorescence (XRF) and/or paint-chip sampling to map where lead-based paint is. A certified risk assessor samples deteriorated paint, dust, and bare soil to identify current hazards and recommend control options. A combination inspection and risk assessment does both. EPA: <a href="https://www.epa.gov/lead/where-can-i-find-qualified-professional-conduct-inspection">Where can I find a qualified professional to conduct an inspection?</a></p>

      <div class="kit-block">
        <p class="kicker">If you buy a consumer device</p>
        <p class="kit-lead">Kits below are consumer products. Only LeadCheck™ is an EPA-recognized RRP test kit, and EPA’s recognition is for trained professionals on listed surfaces. Schneider kits are mail-in laboratory samples, not recognized RRP kits. None of these replaces a certified inspection or risk assessment.</p>
        <div class="kits">
          <article class="kit">
            <p class="kicker">EPA-recognized screen</p>
            <p><span class="rec rec-yes">EPA-recognized (negative result)</span></p>
            <h3>LeadCheck™ Swab Kit (8 swabs)</h3>
            <p>Luxfer Magtech LeadCheck™. Instant color change. EPA recognizes a negative result on wood, ferrous metal, drywall, and plaster when used by a trained professional. A homeowner swab is a screen.</p>
            <p><a class="kit-link" href="https://www.amazon.com/LeadCheck-Swab-Kit/dp/B00AAD5MY6/?tag=radontestinde-20">LeadCheck Swab Kit, ASIN B00AAD5MY6 <span class="paid">(paid link)</span></a></p>
          </article>
          <article class="kit">
            <p class="kicker">Mail-in lab · not an RRP kit</p>
            <p><span class="rec rec-no">Not EPA-recognized as an RRP kit</span></p>
            <h3>Schneider Labs asbestos &amp; lead combo</h3>
            <p>Sample collection for one asbestos sample and one lead sample, analyzed at Schneider Laboratories (an NLLAP lab). Lab fees included. This is not a LeadCheck/D-Lead RRP kit and not a certified inspection.</p>
            <p><a class="kit-link" href="https://www.amazon.com/Asbestos-Test-Schneider-Overnight-Shipping/dp/B08T257C5Q/?tag=radontestinde-20">Schneider asbestos &amp; lead combo, ASIN B08T257C5Q <span class="paid">(paid link)</span></a></p>
          </article>
          <article class="kit">
            <p class="kicker">Mail-in lab · not an RRP kit</p>
            <p><span class="rec rec-no">Not EPA-recognized as an RRP kit</span></p>
            <h3>Schneider Labs asbestos, lead, and mold combo</h3>
            <p>One mold sample, one asbestos sample, and one lead sample (paint chip, dust wipe, or soil). Mail-in analysis. Not an EPA-recognized RRP test kit.</p>
            <p><a class="kit-link" href="https://www.amazon.com/dp/B00IJGXO96/?tag=radontestinde-20">Schneider asbestos, lead, and mold combo, ASIN B00IJGXO96 <span class="paid">(paid link)</span></a></p>
          </article>
        </div>
        <p class="meta">As an Amazon Associate I earn from qualifying purchases. ASINs were verified as live Amazon listings on 2026-09-01. D-Lead® is also EPA-recognized; this index did not find a stable consumer Amazon ASIN for it and does not invent one. ESCA Tech sells D-Lead® to distributors. The Massachusetts kit is for Massachusetts inspectors and risk assessors.</p>
      </div>

      <hr>
      <h2>When to hire a certified inspector or risk assessor</h2>
      <p>Hire a certified professional when:</p>
      <ul>
        <li>You are buying or selling pre-1978 housing and want the 10-day inspection opportunity to mean something.</li>
        <li>A child under 6, a pregnant person, or someone with a lead-related medical concern lives or will live in the housing.</li>
        <li>Paint is peeling, chipping, chalking, or will be disturbed by renovation, and you need to know whether it is a hazard — not just whether a swab changed color.</li>
        <li>You need a report that maps lead-based paint (inspection), current hazards (risk assessment), or both.</li>
        <li>A kit result is positive, inconclusive, or was used on a surface EPA did not evaluate.</li>
      </ul>
      <p>In Michigan, use this index’s <a href="michigan.html">transcribed MDHHS lists</a> ({N_MI} people). In every other state, use <a href="verify.html">EPA’s Lead-based Paint Professional Locator</a> or your state lead program. Always verify the certificate is still current before you hire.</p>
      <p>If the report says to take samples of paint, dust, or soil, ship them to an <a href="labs.html">NLLAP-recognized laboratory</a> accredited for that matrix.</p>
      <hr>
      <h2>What this site does not do</h2>
      <p>Lead Paint Index does not rank contractors, take referral fees, or sell inspections. Amazon Associates links appear only on this how-to page. There are no tracking phone numbers and no click-to-call buttons. Always verify a professional’s credential with EPA or the state program that issued it.</p>
      <p>National Lead Information Center: 1-800-424-LEAD (1-800-424-5323). That is EPA’s public number, printed here as text.</p>
""".replace("{N_MI}", str(N_MI))
    return page(
        "How to Test for Lead Paint with a Kit | Lead Paint Index",
        "How to test a pre-1978 home for lead-based paint: EPA-recognized kits vs a certified inspector or risk assessor. HUD/EPA disclosure. Compiled by Stephen Shortell.",
        "how-to.html",
        body,
        main_class="prose",
    )


def labs_page() -> str:
    from collections import defaultdict

    groups: dict[str, list] = defaultdict(list)
    for lab in LABS:
        groups[lab["state"]].append(lab)
    order = sorted(groups, key=lambda s: (groups[s][0]["state_name"], s))

    toc = []
    blocks = []
    for code in order:
        name = groups[code][0]["state_name"]
        n = sum(1 for l in groups[code] if not l.get("duplicate_of_row"))
        n_rows = len(groups[code])
        label = f"{name} ({n}" + (" unique" if n_rows != n else "") + ")"
        toc.append(f'<a href="#st-{escape(code)}">{escape(label)}</a>')
        rows_html = []
        for lab in groups[code]:
            dup = ""
            if lab.get("duplicate_of_row"):
                dup = ' <span class="dup">duplicate row on EPA table</span>'
            comm = lab["commercial"] or "—"
            phone = escape(lab["phone"]) if lab["phone"] else "—"
            rows_html.append(
                "<tr class=\"pro\" data-hay=\"{hay}\" data-paint=\"{p}\" data-soil=\"{s}\" data-dust=\"{d}\" data-comm=\"{c}\">"
                '<td class="name name-cell" data-label="Laboratory">{co}{dup}</td>'
                '<td class="city" data-label="City">{city}</td>'
                '<td data-label="Matrices">{mx}</td>'
                '<td data-label="Commercial">{comm}</td>'
                '<td class="phone" data-label="Phone">{phone}</td>'
                '<td class="src" data-label="Accrediting">{acc}</td>'
                "</tr>".format(
                    hay=hay(lab["company"], lab["city"], lab["state"], lab["state_name"], lab["as_printed"]),
                    p="1" if lab["paint"] else "0",
                    s="1" if lab["soil"] else "0",
                    d="1" if lab["dust"] else "0",
                    c=escape(lab["commercial"] or ""),
                    co=escape(lab["company"]),
                    dup=dup,
                    city=escape(lab["city"] or "—"),
                    mx=matrices(lab),
                    comm=escape(comm),
                    phone=phone,
                    acc=escape(lab["accred"]),
                )
            )
        extra = ""
        if n_rows != n:
            extra = f" {n_rows} rows as printed, {n} unique."
        blocks.append(
            f"""
      <h2 class="county" id="st-{escape(code)}">{escape(name)} <span class="meta">({n} unique lab{"s" if n != 1 else ""})</span></h2>
      <p class="meta">State/country code on the EPA table: {escape(code)}.{extra}</p>
      <div class="table-scroll">
        <table class="dir">
          <thead>
            <tr>
              <th>Laboratory</th>
              <th>City</th>
              <th>Matrices</th>
              <th>Commercial</th>
              <th>Phone</th>
              <th>Accrediting organization</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>"""
        )

    body = f"""
      <p class="kicker">EPA National Lead Laboratory Accreditation Program</p>
      <h1>NLLAP-recognized lead laboratories</h1>
      <p class="lede">{N_UNIQUE} unique laboratories transcribed from EPA’s NLLAP list, Round 131 (July 2026, month 1 of 3), last updated August 4, 2026. {N_ROWS} rows as printed, including {LAB_META['duplicate_rows']} duplicate rows. Retrieved 2026-09-01. No invented labs. No paid placement.</p>
      <p>EPA established NLLAP so inspectors, risk assessors, and the public can find laboratories recognized to analyze <strong>paint chips, dust wipes, and/or soil</strong> for lead. HUD and EPA rules that require laboratory analysis of those matrices require an NLLAP-recognized lab. Confirm the lab is still recognized for the matrix you are sending before you ship a sample.</p>
      <p>Phones are copied as EPA printed them. They are not tracking numbers and are not click-to-call links.</p>
      <ul>
        <li>Source: <a href="https://www.epa.gov/lead/national-lead-laboratory-accreditation-program-list">National Lead Laboratory Accreditation Program List</a> (updated 2026-08-04; retrieved 2026-09-01)</li>
        <li>Program: <a href="https://www.epa.gov/lead/nllap">The National Lead Laboratory Accreditation Program (NLLAP)</a></li>
      </ul>
      <p class="meta">{LAB_META['commercial_yes']} listings marked commercially available; {LAB_META['commercial_no']} marked not commercially available; one listing has a blank commercial field as printed. Matrices as marked on the table: paint chips {LAB_META['paint']}, soil {LAB_META['soil']}, dust wipes {LAB_META['dust']} (row counts, including duplicates).</p>

      <div class="filters" role="search">
        <label class="field">Search laboratory, city, or state
          <input type="search" id="q" placeholder="Name, city, or state" autocomplete="off">
        </label>
        <div class="pills" role="radiogroup" aria-label="Filter by matrix">
          <label><input type="radio" name="mx" value="all" checked> <span>All matrices</span></label>
          <label><input type="radio" name="mx" value="paint"> <span>Paint chips</span></label>
          <label><input type="radio" name="mx" value="soil"> <span>Soil</span></label>
          <label><input type="radio" name="mx" value="dust"> <span>Dust wipes</span></label>
        </div>
      </div>
      <p class="shown" id="shown" aria-live="polite">Showing {N_ROWS} of {N_ROWS}</p>
      <p class="meta">Jump to: {" · ".join(toc)}</p>
      {"".join(blocks)}
      <script>
(function () {{
  var q = document.getElementById("q");
  var shown = document.getElementById("shown");
  var rows = document.querySelectorAll("tr.pro");
  var total = rows.length;
  var radios = document.querySelectorAll("input[name='mx']");
  function val() {{
    var r = document.querySelector("input[name='mx']:checked");
    return r ? r.value : "all";
  }}
  function run() {{
    var needle = (q.value || "").trim().toLowerCase();
    var filter = val();
    var n = 0;
    for (var i = 0; i < rows.length; i++) {{
      var row = rows[i];
      var hay = row.getAttribute("data-hay") || "";
      var okMx = filter === "all" || row.getAttribute("data-" + filter) === "1";
      var ok = okMx && (!needle || hay.indexOf(needle) !== -1);
      row.hidden = !ok;
      if (ok) n++;
    }}
    if (shown) shown.textContent = "Showing " + n + " of " + total;
  }}
  if (q) q.addEventListener("input", run);
  for (var i = 0; i < radios.length; i++) radios[i].addEventListener("change", run);
  run();
}})();
      </script>
"""
    return page(
        "EPA NLLAP Lead Laboratories | Lead Paint Index",
        f"{N_UNIQUE} unique EPA-recognized NLLAP laboratories transcribed from Round 131 (updated August 4, 2026). No paid placement.",
        "labs.html",
        body,
    )


def michigan_page() -> str:
    from collections import OrderedDict

    insp = [p for p in PEOPLE if p["role"] == "inspector"]
    dual = [p for p in PEOPLE if p["role"] == "inspector/risk assessor"]

    def group(people):
        g: OrderedDict[str, list] = OrderedDict()
        for p in people:
            g.setdefault(p["county"], []).append(p)
        return g

    def table_for(people, role_slug):
        g = group(people)
        parts = []
        for county, rows in g.items():
            trs = []
            for p in rows:
                phone = escape(p["phone"]) if p["phone"] else escape(p["phone_as_printed"] or "Not Listed")
                name = escape(p["name"])
                trs.append(
                    "<tr class=\"pro\" data-hay=\"{hay}\" data-role=\"{role}\">"
                    '<td class="name name-cell" data-label="Name">{name}</td>'
                    '<td data-label="Firm">{firm}</td>'
                    '<td class="city" data-label="City">{city}</td>'
                    '<td class="cred" data-label="Cert #">{cert}</td>'
                    '<td class="phone" data-label="Phone">{phone}</td>'
                    "</tr>".format(
                        hay=hay(p["name"], p["firm"], p["city"], p["county"], p["cert"], p["role"]),
                        role=role_slug,
                        name=name,
                        firm=escape(p["firm"]),
                        city=escape(p["city"]),
                        cert=escape(p["cert"]),
                        phone=phone,
                    )
                )
            parts.append(
                f'<h3 class="county">{escape(county)} <span class="meta">({len(rows)})</span></h3>\n'
                f'<div class="table-scroll"><table class="dir"><thead><tr>'
                f"<th>Name</th><th>Firm</th><th>City</th><th>Cert #</th><th>Phone</th>"
                f"</tr></thead><tbody>{''.join(trs)}</tbody></table></div>"
            )
        return "\n".join(parts)

    body = f"""
      <p class="kicker">Michigan Department of Health and Human Services · MiLeadSafe</p>
      <h1>Michigan certified lead inspectors and risk assessors</h1>
      <p class="lede">{N_MI} people transcribed from MDHHS lists updated 2026-08-27: {N_INSP} certified lead inspectors (inspector only) and {N_DUAL} certified lead inspector/risk assessors (dual certification). Retrieved 2026-09-01. No invented names. No paid placement.</p>
      <p>MDHHS: a certified inspector uses an XRF instrument to measure and identify lead. A certified risk assessor uses those findings to determine whether any lead found is a lead hazard. Some people hold both certifications; they appear only on the dual list.</p>
      <p>County headings are as MDHHS printed them (address of record). Some certificate holders are based outside Michigan. Phones are copied as printed; “Not Listed” is the state’s phrase. They are not tracking numbers and are not click-to-call links.</p>
      <ul>
        <li><a href="https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional">Hire a Lead Professional</a> (lists updated 2026-08-27)</li>
        <li><a href="https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional/certified-lead-inspectors">Certified Lead Inspectors</a></li>
        <li><a href="https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional/certified-lead-inspector-risk-assessors">Certified Lead Inspector/Risk Assessors</a></li>
      </ul>
      <p>Always verify the certificate is still current with MDHHS before hiring. For other states, use the <a href="verify.html">EPA locator</a>.</p>

      <div class="filters" role="search">
        <label class="field">Search name, firm, city, or cert #
          <input type="search" id="q" placeholder="Name, firm, city, or cert #" autocomplete="off">
        </label>
        <div class="pills" role="radiogroup" aria-label="Filter by credential">
          <label><input type="radio" name="role" value="all" checked> <span>All ({N_MI})</span></label>
          <label><input type="radio" name="role" value="inspector"> <span>Inspector only ({N_INSP})</span></label>
          <label><input type="radio" name="role" value="dual"> <span>Inspector/risk assessor ({N_DUAL})</span></label>
        </div>
      </div>
      <p class="shown" id="shown" aria-live="polite">Showing {N_MI} of {N_MI}</p>

      <h2 id="inspectors">Certified lead inspectors (inspector only) — {N_INSP}</h2>
      {table_for(insp, "inspector")}

      <h2 id="dual">Certified lead inspector/risk assessors — {N_DUAL}</h2>
      {table_for(dual, "dual")}
      <script>
(function () {{
  var q = document.getElementById("q");
  var shown = document.getElementById("shown");
  var rows = document.querySelectorAll("tr.pro");
  var total = rows.length;
  var radios = document.querySelectorAll("input[name='role']");
  function val() {{
    var r = document.querySelector("input[name='role']:checked");
    return r ? r.value : "all";
  }}
  function run() {{
    var needle = (q.value || "").trim().toLowerCase();
    var filter = val();
    var n = 0;
    for (var i = 0; i < rows.length; i++) {{
      var row = rows[i];
      var hay = row.getAttribute("data-hay") || "";
      var role = row.getAttribute("data-role") || "";
      var okRole = filter === "all" || role === filter;
      var ok = okRole && (!needle || hay.indexOf(needle) !== -1);
      row.hidden = !ok;
      if (ok) n++;
    }}
    if (shown) shown.textContent = "Showing " + n + " of " + total;
  }}
  if (q) q.addEventListener("input", run);
  for (var i = 0; i < radios.length; i++) radios[i].addEventListener("change", run);
  run();
}})();
      </script>
"""
    return page(
        "Michigan Certified Lead Inspectors | Lead Paint Index",
        f"{N_MI} Michigan certified lead inspectors and inspector/risk assessors transcribed from MDHHS lists updated 2026-08-27. No paid placement.",
        "michigan.html",
        body,
    )


def verify_page() -> str:
    body = """
      <h1>Verify a certified lead professional</h1>
      <p>This index transcribes lists that EPA and Michigan publish as tables. EPA’s national firm locator is a search form, not a downloadable roster. We did not scrape it and we do not invent inspectors for states that only have that form.</p>
      <h2>EPA Lead-based Paint Professional Locator</h2>
      <p>EPA’s locator is the official search for certified firms (renovation, dust sampling, abatement, inspection, and risk assessment). It is a multi-step form. Some states, tribes, and territories run their own authorized programs; the locator points you there.</p>
      <ul>
        <li>Current host (as of retrieval 2026-09-01): <a href="https://cdxocsppapps.epa.gov/ocspp-oppt-lead/firm-location-search">https://cdxocsppapps.epa.gov/ocspp-oppt-lead/firm-location-search</a></li>
        <li>URL EPA still publishes in consumer materials, which redirects: <a href="https://cdxapps.epa.gov/ocspp-oppt-lead/firm-location-search">https://cdxapps.epa.gov/ocspp-oppt-lead/firm-location-search</a></li>
        <li>EPA FAQ: <a href="https://www.epa.gov/lead/where-can-i-find-qualified-professional-conduct-inspection">Where can I find a qualified professional to conduct an inspection?</a></li>
      </ul>
      <p>Confirm the firm or individual is currently certified before you hire. EPA also maintains a list of entities whose certification has been suspended, revoked, modified, or reinstated; the locator page links that list.</p>
      <h2>What this index does ship</h2>
      <ul>
        <li><a href="labs.html">{n} unique NLLAP laboratories</a> from EPA’s published table (Round 131, updated 2026-08-04).</li>
        <li><a href="michigan.html">{mi} Michigan certified inspectors and inspector/risk assessors</a> from MDHHS lists updated 2026-08-27.</li>
      </ul>
      <h2>National Lead Information Center</h2>
      <p>1-800-424-LEAD (1-800-424-5323). Printed as text, not a click-to-call or tracking number.</p>
""".replace("{n}", str(N_UNIQUE)).replace("{mi}", str(N_MI))
    return page(
        "Verify a Lead Professional | Lead Paint Index",
        "Use EPA’s Lead-based Paint Professional Locator to verify certified firms. This index does not scrape the JS search form.",
        "verify.html",
        body,
        main_class="prose",
    )


def about_page() -> str:
    body = f"""
      <h1>About Lead Paint Index</h1>
      <p>Lead Paint Index is an <strong>independent public directory</strong> compiled by <strong>Stephen Shortell</strong>. It lists laboratories and people who already appear on official EPA and Michigan lists. It is a reading of those records, not a new credential.</p>
      <h2>What this is not</h2>
      <ul>
        <li>Not a laboratory and not a lead inspection, risk assessment, or abatement company.</li>
        <li>Not Shortell Designs, and not a product or service of any design studio.</li>
        <li>Not endorsed by the U.S. Environmental Protection Agency, HUD, MDHHS, or any state lead program.</li>
        <li>Not a ranking, marketplace, or referral desk. There is no paid placement on laboratory or professional lists.</li>
        <li>Not Exclusive Live Calls. There is no live-call page, no tracking numbers, and no click-to-call.</li>
      </ul>
      <h2>Where the names come from</h2>
      <p>Retrieved 2026-09-01.</p>
      <ul>
        <li><strong>NLLAP laboratories:</strong> {N_ROWS} rows ({N_UNIQUE} unique labs; {LAB_META['duplicate_rows']} duplicate rows as EPA printed them) from the <a href="https://www.epa.gov/lead/national-lead-laboratory-accreditation-program-list">National Lead Laboratory Accreditation Program List</a>, Round 131, July 2026 (month 1 of 3), last updated August 4, 2026. Company, city, phone, matrices, commercial availability, and accrediting-organization code as printed. City was split from EPA’s combined “Company Name, City &amp; Phone” cell; the original cell is stored in the data file.</li>
        <li><strong>Michigan:</strong> {N_INSP} certified lead inspectors and {N_DUAL} certified lead inspector/risk assessors from MDHHS MiLeadSafe lists updated August 27, 2026. Cert #, name, firm, city, county heading, and phone as printed.</li>
        <li><strong>EPA firm locator:</strong> not transcribed. It is a JavaScript search form. See <a href="verify.html">Verify a pro</a>.</li>
      </ul>
      <p>No laboratory, inspector, phone number, accreditation, or certificate number was invented. Phone numbers from the official lists are republished as text only.</p>
      <h2>Amazon Associates</h2>
      <p>How-to page product links are Amazon Associates Special Links using tag <code>radontestinde-20</code>. As an Amazon Associate I earn from qualifying purchases. Those links do not appear on laboratory or professional lists. EPA-recognized versus not-recognized status is disclosed next to each kit.</p>
      <h2>Contact</h2>
      <p>Questions about the compilation: Stephen Shortell. For certification questions, use EPA, the National Lead Information Center (1-800-424-LEAD), or the state lead program — not this index.</p>
"""
    return page(
        "About — Lead Paint Index",
        "Independent lead-paint directory compiled by Stephen Shortell. Not a lab, not EPA-endorsed. Verify credentials with EPA or the state program.",
        "about.html",
        body,
        main_class="prose",
    )


def write_readme() -> str:
    return f"""# Lead Paint Index

A public directory of **EPA-recognized NLLAP lead laboratories** and **Michigan certified lead inspectors / inspector-risk assessors**.

Compiled from official lists. Names are transcribed from those sources. No invented labs or people.

**By Stephen Shortell**

Live: https://shortelldesigns.github.io/lead-paint-index/

---

## What’s here

| File | Contents |
| --- | --- |
| `data/nllap.json` | EPA NLLAP Round 131 table (updated 2026-08-04, retrieved 2026-09-01) |
| `data/michigan.json` | MDHHS certified inspectors and inspector/risk assessors (lists updated 2026-08-27) |
| `how-to.html` | Original guide: pre-1978 housing, HUD/EPA disclosure, kits vs certified inspection |

---

## Counts (retrieved 2026-09-01)

| List | Records |
| --- | ---: |
| NLLAP rows as printed | {N_ROWS} |
| NLLAP unique laboratories | {N_UNIQUE} |
| Michigan inspector only | {N_INSP} |
| Michigan inspector/risk assessor | {N_DUAL} |
| Michigan total | {N_MI} |

EPA printed {LAB_META['duplicate_rows']} duplicate laboratory rows (same company, city, and phone). Unique count drops those rows.

The EPA Lead-based Paint Professional Locator is a JavaScript search form and is **not** scraped. Use [verify.html](verify.html).

---

## Sources

- [National Lead Laboratory Accreditation Program List](https://www.epa.gov/lead/national-lead-laboratory-accreditation-program-list) — Round 131, July 2026; last updated August 4, 2026
- [Lead Test Kits](https://www.epa.gov/lead/testkits)
- [Real Estate Disclosures about Potential Lead Hazards](https://www.epa.gov/lead/real-estate-disclosures-about-potential-lead-hazards)
- [EPA Lead-based Paint Professional Locator](https://cdxapps.epa.gov/ocspp-oppt-lead/firm-location-search) (redirects to `cdxocsppapps.epa.gov`)
- [MDHHS Hire a Lead Professional](https://www.michigan.gov/mileadsafe/lead-services/hire-lead-professional) — lists updated 2026-08-27

Certification status changes. Confirm a current credential before hiring.

Amazon Associates links appear only on the how-to page. As an Amazon Associate I earn from qualifying purchases. No paid placement on professional or laboratory lists.
"""


def main() -> None:
    (ROOT / "index.html").write_text(index_page())
    (ROOT / "how-to.html").write_text(how_to_page())
    (ROOT / "labs.html").write_text(labs_page())
    (ROOT / "michigan.html").write_text(michigan_page())
    (ROOT / "verify.html").write_text(verify_page())
    (ROOT / "about.html").write_text(about_page())
    (ROOT / "README.md").write_text(write_readme())
    (ROOT / ".nojekyll").write_text("")
    print("wrote pages")


if __name__ == "__main__":
    main()
