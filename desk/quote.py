#!/usr/bin/env python3
"""Overtime Floor Desk — offline 2026 min-wage + FLSA OT quoter.

No network. No API keys. Planning only — not wage-and-hour advice.

  python3 desk/quote.py --list CA
  python3 desk/quote.py --quote TX --hourly 18 --hours 48
  python3 desk/quote.py --quote CA --hourly 22 --hours 45 --days 5 --daily
  python3 desk/quote.py --quote NY --hourly 24 --hours 44 --band downstate
  python3 desk/quote.py --quote FL --hourly 14 --hours 40 --as-of 2026-09-30
  python3 desk/quote.py --batch data/sample_shifts.csv
  python3 desk/quote.py --watch
  python3 desk/quote.py --cheap
  python3 desk/quote.py --high
  python3 desk/quote.py --bands OR
  python3 desk/quote.py --exempt --salary-weekly 650
  python3 desk/quote.py --exempt --salary-weekly 900 --state CA
  python3 desk/quote.py --exempt --list-eap
  python3 desk/quote.py --list-tips TX
  python3 desk/quote.py --tip TX --hours 48
  python3 desk/quote.py --tip NY --band downstate --role food --hours 45
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WAGES = DATA / "min_wages.csv"
BANDS = DATA / "bands.csv"
FLSA = DATA / "flsa.csv"
EAP = DATA / "eap_state.csv"
TIPS = DATA / "tips.csv"

FL_STEP_ON = date(2026, 9, 30)
FL_STEP_RATE = 15.00
EAP_WEEKLY = 684.0
EAP_ANNUAL = 35568.0
HCE_ANNUAL = 107432.0
COMPUTER_HOURLY = 27.63
OT_MULT = 1.5
WEEKLY_OT_HOURS = 40.0
FED_MW = 7.25
FED_TIP_CASH = 2.13
FED_TIP_CREDIT = 5.12


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def flsa_map() -> dict[str, str]:
    return {r["key"]: r["value"] for r in load_csv(FLSA)}


def rows() -> list[dict]:
    return load_csv(WAGES)


def by_abbr() -> dict[str, dict]:
    return {r["abbr"].upper(): r for r in rows()}


def band_rows() -> list[dict]:
    return load_csv(BANDS)


def bands_for(abbr: str) -> list[dict]:
    return [b for b in band_rows() if b["abbr"].upper() == abbr.upper()]


def eap_rows() -> list[dict]:
    return load_csv(EAP)


def eap_for(abbr: str | None, band: str | None) -> dict:
    table = eap_rows()
    fed = next(r for r in table if r["abbr"] == "FED")
    if not abbr or abbr.upper() in ("FED", "US", "FLSA"):
        return fed
    hits = [r for r in table if r["abbr"].upper() == abbr.upper()]
    if not hits:
        return fed
    if band:
        match = next((r for r in hits if r["band"] == band), None)
        if match:
            return match
    default_band = None
    wage = by_abbr().get(abbr.upper())
    if wage:
        default_band = wage.get("default_band")
    if default_band:
        match = next((r for r in hits if r["band"] == default_band), None)
        if match:
            return match
    return hits[0]


def tip_rows() -> list[dict]:
    return load_csv(TIPS)


def tips_for(abbr: str, band: str | None, role: str | None) -> dict:
    hits = [r for r in tip_rows() if r["abbr"].upper() == abbr.upper()]
    if not hits:
        raise SystemExit(f"no tip-credit row for {abbr}")
    if band:
        banded = [r for r in hits if r["band"] == band]
        if banded:
            hits = banded
    if role:
        role_hits = [r for r in hits if r["role"] == role]
        if not role_hits:
            names = sorted({r["role"] for r in hits})
            raise SystemExit(f"unknown --role {role!r} for {abbr}; try: {', '.join(names)}")
        hits = role_hits
    else:
        defaults = [r for r in hits if r["role"] == "default"]
        if defaults:
            hits = defaults
        elif abbr.upper() == "NY":
            food = [r for r in hits if r["role"] == "food"]
            if food:
                hits = food
        elif abbr.upper() == "CT":
            hotel = [r for r in hits if r["role"] == "hotel"]
            if hotel:
                hits = hotel
    return hits[0]


def tip_ot_cash(row: dict, ot_hours: float) -> dict:
    combined = float(row["combined_mw"])
    credit = float(row["max_tip_credit"])
    cash = float(row["cash_wage"])
    kind = row.get("credit_kind") or "flsa"
    ot_full_c = cents(OT_MULT * combined)
    credit_c = cents(credit)
    ot_cash_c = ot_full_c if kind == "none" else ot_full_c - credit_c
    ot_full = ot_full_c / 100.0
    ot_cash = ot_cash_c / 100.0
    note = (
        "29 CFR 531.60 / WHD Fact Sheet #15: regular rate includes the tip credit "
        "taken (not excess tips). Cash OT = 1.5× combined MW − max tip credit "
        "(nearest cent). Straight-time cash stays at the cited cash wage."
    )
    if kind == "none":
        note = (
            "No tip credit in this jurisdiction. Cash wage = full MW; OT cash = 1.5× MW. "
            "Tips sit on top and are not a credit against the floor."
        )
    return {
        "combined": combined,
        "credit": credit,
        "cash": cash,
        "ot_full": ot_full,
        "ot_cash": ot_cash,
        "ot_hours": ot_hours,
        "straight_cash_gross": cents(cash * max(0.0, WEEKLY_OT_HOURS)) / 100.0,
        "ot_cash_gross": cents(ot_cash * ot_hours) / 100.0,
        "kind": kind,
        "note": note,
    }


def parse_as_of(s: str | None) -> date:
    if not s:
        return datetime.now().date()
    return datetime.strptime(s, "%Y-%m-%d").date()


def cents(n: float) -> int:
    return int(round(n * 100 + 1e-9))


def money(n: float) -> str:
    c = cents(n)
    sign = "-" if c < 0 else ""
    c = abs(c)
    return f"{sign}${c // 100:,}.{c % 100:02d}"


def overlay_as_of(row: dict, as_of: date) -> dict:
    r = dict(row)
    if r.get("abbr") == "FL" and as_of >= FL_STEP_ON:
        r["standard_mw"] = f"{FL_STEP_RATE:.2f}"
        r["effective"] = "2026-09-30"
        r["next_step"] = ""
        r["next_date"] = ""
        r["notes"] = (
            "Fla. Const. Art. X §24 remaining step: $15.00 on 2026-09-30. "
            "DOL July 1 table still listed $14.00."
        )
        r["source_id"] = "FL-ART-X-24"
    return r


def apply_band(row: dict, band: str | None) -> dict:
    r = dict(row)
    abbr = r["abbr"]
    options = bands_for(abbr)
    if not options:
        if band:
            raise SystemExit(f"{abbr} has no DOL-footnote bands (got --band {band})")
        return r
    if not band:
        band = r.get("default_band") or "standard"
    match = next((b for b in options if b["band"] == band), None)
    if match is None:
        names = ", ".join(b["band"] for b in options)
        raise SystemExit(f"unknown band {band!r} for {abbr}; try: {names}")
    r["standard_mw"] = match["standard_mw"]
    r["default_band"] = match["band"]
    r["notes"] = match["notes"]
    r["effective"] = match["effective"]
    return r


def mw_of(row: dict) -> float:
    return float(row["standard_mw"])


def floor_status(hourly: float, floor: float) -> str:
    if hourly + 1e-9 < floor:
        return "UNDER_FLOOR"
    if abs(hourly - floor) < 1e-9:
        return "AT_FLOOR"
    return "ABOVE_FLOOR"


def daily_ot_hours(hours: float, days: int) -> tuple[float, float]:
    if days <= 0:
        return 0.0, 0.0
    per = hours / days
    over8 = max(0.0, per - 8.0) * days
    over12 = max(0.0, per - 12.0) * days
    return over8, over12


def quote_pay(
    *,
    hourly: float,
    hours: float,
    days: int,
    row: dict,
    daily: bool,
    over8: float | None,
    over12: float | None,
) -> dict:
    floor = mw_of(row)
    status = floor_status(hourly, floor)
    weekly_ot = max(0.0, hours - WEEKLY_OT_HOURS)
    straight = min(hours, WEEKLY_OT_HOURS)
    kind = row.get("daily_ot") or "flsa_40"
    use_daily = daily or kind not in ("flsa_40",)
    if over8 is None or over12 is None:
        est8, est12 = daily_ot_hours(hours, days)
        if over8 is None:
            over8 = est8
        if over12 is None:
            over12 = est12

    premium_hours = 0.0
    double_hours = 0.0
    note = "FLSA 40-hour week only (1.5×)."

    if use_daily and kind == "after_8_dt12":
        # CA: 1.5 after 8, 2.0 after 12; weekly 40 also applies.
        double_hours = over12
        daily_15 = max(0.0, over8 - over12)
        premium_hours = max(weekly_ot, daily_15 + double_hours)
        # Pay: straight to 8/day, 1.5 between 8-12, 2.0 after 12, but never
        # undercount weekly OT. Model: all hours at hourly, plus 0.5× on
        # premium_hours, plus extra 0.5× on double_hours (to reach 2.0).
        note = (
            "CA Labor Code §510 overlay: 1.5× after 8/day, 2× after 12/day, "
            "and 40-hour week. Even-split day estimate unless --over-8/--over-12 set."
        )
        extra = 0.5 * max(weekly_ot, daily_15) + 1.0 * double_hours
        # If weekly OT exceeds daily premium hours, pay the weekly 0.5× on the rest.
        if weekly_ot > daily_15 + double_hours:
            extra = 0.5 * weekly_ot + 0.5 * double_hours
        pay = hourly * hours + extra * hourly
        return {
            "floor": floor,
            "status": status,
            "straight_hours": hours - (daily_15 + double_hours)
            if daily_15 + double_hours <= hours
            else max(0.0, hours - weekly_ot),
            "ot_15_hours": daily_15 if weekly_ot <= daily_15 + double_hours else max(0.0, weekly_ot - double_hours),
            "ot_20_hours": double_hours,
            "gross": pay,
            "note": note,
            "kind": kind,
        }

    if use_daily and kind == "after_8":
        premium_hours = max(weekly_ot, over8)
        note = "Alaska AS 23.10.060 overlay: 1.5× after 8/day and after 40/week."
    elif use_daily and kind == "after_12":
        premium_hours = max(weekly_ot, over12)
        note = "Colorado COMPS overlay: 1.5× after 12/day and after 40/week."
    elif use_daily and kind == "after_8_if_low":
        if hourly + 1e-9 < 1.5 * floor:
            premium_hours = max(weekly_ot, over8)
            note = (
                "Nevada NRS 608.018: regular rate < 1.5× MW, so 1.5× after 8/day "
                "and after 40/week."
            )
        else:
            premium_hours = weekly_ot
            note = (
                "Nevada NRS 608.018: regular rate ≥ 1.5× MW, so weekly 40 only."
            )
    else:
        premium_hours = weekly_ot

    extra = 0.5 * premium_hours
    pay = hourly * hours + extra * hourly
    return {
        "floor": floor,
        "status": status,
        "straight_hours": hours - premium_hours,
        "ot_15_hours": premium_hours,
        "ot_20_hours": 0.0,
        "gross": pay,
        "note": note,
        "kind": kind if use_daily else "flsa_40",
    }


def print_row(row: dict) -> None:
    print(
        f"{row['abbr']:3} {row['state']:<22} {money(mw_of(row)):>8}  "
        f"band={row.get('default_band','statewide'):<14}  "
        f"daily={row.get('daily_ot','flsa_40'):<14}  "
        f"next={row.get('next_step') or '—'} {row.get('next_date') or ''}".rstrip()
    )


def cmd_list(abbr: str | None, as_of: date) -> None:
    table = rows()
    if abbr:
        r = by_abbr().get(abbr.upper())
        if not r:
            raise SystemExit(f"unknown state {abbr}")
        r = overlay_as_of(r, as_of)
        print_row(r)
        print(r.get("notes") or "")
        print(f"source: {r.get('authority')}")
        return
    print(f"as_of={as_of.isoformat()}  federal_floor={money(FED_MW)}  source=DOL WHD 2026-07-01")
    for r in table:
        print_row(overlay_as_of(r, as_of))


def cmd_bands(abbr: str) -> None:
    opts = bands_for(abbr)
    if not opts:
        print(f"{abbr.upper()} has no DOL-footnote bands (statewide row only).")
        return
    for b in opts:
        print(
            f"{b['abbr']}  {b['band']:<14} {money(float(b['standard_mw'])):>8}  "
            f"{b['label']}  ({b['notes']})"
        )


def cmd_quote(args: argparse.Namespace) -> None:
    abbr = args.quote.upper()
    raw = by_abbr().get(abbr)
    if not raw:
        raise SystemExit(f"unknown state {abbr}")
    as_of = parse_as_of(args.as_of)
    row = apply_band(overlay_as_of(raw, as_of), args.band)
    hourly = float(args.hourly)
    hours = float(args.hours)
    days = int(args.days)
    q = quote_pay(
        hourly=hourly,
        hours=hours,
        days=days,
        row=row,
        daily=bool(args.daily),
        over8=None if args.over_8 is None else float(args.over_8),
        over12=None if args.over_12 is None else float(args.over_12),
    )
    print(f"state={abbr} band={row.get('default_band')} as_of={as_of.isoformat()}")
    print(f"floor={money(q['floor'])}  hourly={money(hourly)}  {q['status']}")
    print(
        f"hours={hours:g} days={days}  straight={q['straight_hours']:g}  "
        f"ot_1.5={q['ot_15_hours']:g}  ot_2.0={q['ot_20_hours']:g}"
    )
    print(f"gross={money(q['gross'])}")
    print(q["note"])
    if q["status"] == "UNDER_FLOOR":
        print(
            f"WARNING: hourly {money(hourly)} is under {abbr} floor {money(q['floor'])}."
        )


def cmd_batch(path: Path, daily_flag: bool) -> None:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        print(
            "name,state,band,hourly,hours,floor,status,ot_1.5,ot_2.0,gross,exempt_flag"
        )
        for rec in reader:
            abbr = rec["state"].upper()
            raw = by_abbr().get(abbr)
            if not raw:
                print(f"{rec.get('name')},{abbr},UNKNOWN,,,,,,,")
                continue
            as_of = parse_as_of(rec.get("as_of") or None)
            band = rec.get("band") or None
            if band in ("", "statewide"):
                band = None
            row = apply_band(overlay_as_of(raw, as_of), band)
            hourly = float(rec["hourly"])
            hours = float(rec["hours"])
            days = int(rec.get("days") or 5)
            over8 = rec.get("hours_over_8")
            over12 = rec.get("hours_over_12")
            q = quote_pay(
                hourly=hourly,
                hours=hours,
                days=days,
                row=row,
                daily=daily_flag or row.get("daily_ot") not in ("flsa_40",),
                over8=None if over8 in (None, "") else float(over8),
                over12=None if over12 in (None, "") else float(over12),
            )
            salary = rec.get("salary_weekly") or ""
            exempt = ""
            if salary.strip():
                sw = float(salary)
                eap = eap_for(abbr, row.get("default_band"))
                floor = max(EAP_WEEKLY, float(eap["weekly"]))
                tag = eap["abbr"] if float(eap["weekly"]) > EAP_WEEKLY else "FED"
                exempt = (
                    f"BELOW_{tag}_EAP"
                    if sw + 1e-9 < floor
                    else f"MEETS_{tag}_EAP_SALARY"
                )
            print(
                f"{rec.get('name')},{abbr},{row.get('default_band')},{hourly:.2f},"
                f"{hours:g},{q['floor']:.2f},{q['status']},{q['ot_15_hours']:g},"
                f"{q['ot_20_hours']:g},{q['gross']:.2f},{exempt}"
            )


def cmd_watch() -> None:
    print("2026 overtime-floor watch (cited, not invented)")
    print(
        f"- FL remaining Amendment 2 step: $14.00 → $15.00 on {FL_STEP_ON.isoformat()} "
        "(Fla. Const. Art. X §24). DOL July 1 table still lists $14.00."
    )
    print(
        f"- EAP salary level restored to {money(EAP_WEEKLY)}/week "
        f"({money(EAP_ANNUAL)}/year) after courts vacated the 2024 rule; "
        "DOL technical amendment 2026-05-14 / 91 FR 27833."
    )
    print(f"- HCE total annual compensation {money(HCE_ANNUAL)}.")
    print(f"- Computer hourly exemption {money(COMPUTER_HOURLY)}.")
    print(
        "- State EAP salary floors (higher than $684, cited): "
        "WA $1,541.70 (2.25× $17.13 × 40, L&I 2026); "
        "CA $1,352 (2× $16.90 × 40, Lab. Code §515); "
        "NY downstate $1,275 / rest $1,199.10 (exec/admin); "
        "CO $1,111.23 (7 CCR 1103-14 PAY CALC row E); "
        "AK $1,120 (AS 23.10.055(b) 2× $14 × 40 after 2026-07-01); "
        "ME $871.16 (26 M.R.S. §663(3)(K) 3000× $15.10)."
    )
    print(
        "- CA computer 515.5: $58.85/hr or $122,573.13/yr (DIR OPRL 2026-01-01). "
        "WA computer $59.96/hr (L&I). CO computer $34.85/hr or EAP weekly; "
        "CO HCE $130,014 (PAY CALC row G). CA has no state HCE."
    )
    print("- Highest DOL July 1 statewide listed: DC $18.40; next WA $17.13.")
    print("- NY split: downstate $17.00 / rest $16.00 (DOL fn.5).")
    print("- OR split: Portland $16.80 / standard $15.55 / nonurban $14.55 (DOL fn.7).")
    print("- NJ split: ≥6 employees $15.92 / <6 or seasonal $15.23 (DOL fn.4).")
    print("- OH small-employer $7.25 if gross receipts under $405,000 (DOL fn.6).")
    print(
        f"- FLSA tip credit still $2.13 cash / ${FED_TIP_CREDIT:.2f} credit "
        "(DOL WHD tipped table 2026-07-01). Federal OT cash on $7.25 = "
        f"{money(OT_MULT * FED_MW - FED_TIP_CREDIT)}/hr "
        "(1.5× MW − credit; 29 CFR 531.60)."
    )
    print(
        "- No-credit cash = full MW: AK $14.00, CA $16.90, MN $11.41, MT $10.85, "
        "NV $12.00, OR $16.80/$15.55/$14.55, WA $17.13, GU $9.25 (territories not in 51-row)."
    )
    print(
        "- NY hospitality 2026-01-01 (NY DOL, not the blank DOL tipped cell): "
        "downstate food $11.35 cash / $5.65 credit; service $14.15 / $2.85; "
        "rest food $10.70 / $5.30; rest service $13.30 / $2.70."
    )
    print(
        "- CT split on DOL table: hotel/restaurant cash $6.38 / $10.56 credit; "
        "bartenders $8.23 / $8.71. HI $1.25 credit only if cash+tips ≥ MW+$7."
    )


def cmd_cheap() -> None:
    print("Jurisdictions at the FLSA $7.25 floor on DOL 2026-07-01 table:")
    for r in rows():
        if mw_of(r) == FED_MW:
            print(f"  {r['abbr']}  {r['state']:<22} {r['has_state_mw']}")


def cmd_high() -> None:
    ranked = sorted(rows(), key=lambda r: mw_of(r), reverse=True)
    print("Highest default statewide floors (DOL 2026-07-01):")
    for r in ranked[:12]:
        print(f"  {r['abbr']}  {money(mw_of(r)):>8}  {r['state']}")


def cmd_list_eap() -> None:
    print("2026 EAP salary floors (federal $684 is always the floor; state may be higher)")
    print(f"{'jurisdiction':<22} {'weekly':>10} {'annual':>12}  formula")
    for r in eap_rows():
        label = f"{r['abbr']}/{r['band']}"
        print(
            f"{label:<22} {money(float(r['weekly'])):>10} "
            f"{money(float(r['annual'])):>12}  {r['formula']}"
        )


def cmd_list_tips(abbr: str | None) -> None:
    table = tip_rows()
    if abbr:
        hits = [r for r in table if r["abbr"].upper() == abbr.upper()]
        if not hits:
            raise SystemExit(f"unknown state {abbr}")
        table = hits
    print(
        f"{'jurisdiction':<22} {'role':<10} {'MW':>7} {'cash':>7} {'credit':>7}  "
        f"{'ot_cash':>8}  kind"
    )
    for r in table:
        ot = tip_ot_cash(r, 0.0)
        label = f"{r['abbr']}/{r['band']}"
        print(
            f"{label:<22} {r['role']:<10} {money(ot['combined']):>7} "
            f"{money(ot['cash']):>7} {money(ot['credit']):>7}  "
            f"{money(ot['ot_cash']):>8}  {ot['kind']}"
        )


def cmd_tip(args: argparse.Namespace) -> None:
    abbr = args.tip.upper()
    hours = float(args.hours)
    ot_hours = max(0.0, hours - WEEKLY_OT_HOURS)
    row = tips_for(abbr, args.band, args.role)
    q = tip_ot_cash(row, ot_hours)
    print(
        f"state={abbr} band={row['band']} role={row['role']} "
        f"hours={hours:g} ot_hours={ot_hours:g}"
    )
    print(
        f"combined_mw={money(q['combined'])}  cash_wage={money(q['cash'])}  "
        f"max_credit={money(q['credit'])}  kind={q['kind']}"
    )
    print(
        f"ot_full_rate={money(q['ot_full'])}  ot_cash_rate={money(q['ot_cash'])}  "
        f"(1.5× MW − credit)"
    )
    print(
        f"straight_cash_on_40={money(q['straight_cash_gross'])}  "
        f"ot_cash_gross={money(q['ot_cash_gross'])}  "
        f"employer_cash={money(q['straight_cash_gross'] + q['ot_cash_gross'])}"
    )
    print(q["note"])
    print(f"source: {row.get('authority')}")
    print(row.get("notes") or "")
    if q["kind"] != "none" and args.hourly is not None:
        paid = float(args.hourly)
        if paid + 1e-9 < q["cash"]:
            print(
                f"WARNING: cash hourly {money(paid)} is under cited cash floor "
                f"{money(q['cash'])}."
            )


def cmd_exempt(
    salary_weekly: float,
    hourly: float | None,
    state: str | None,
    band: str | None,
) -> None:
    fed_w = EAP_WEEKLY
    eap = eap_for(state, band)
    state_w = float(eap["weekly"])
    floor = max(fed_w, state_w)
    print(f"federal EAP weekly: {money(fed_w)}  (annual {money(EAP_ANNUAL)})")
    print(f"federal HCE annual: {money(HCE_ANNUAL)}")
    print(f"federal computer hourly: {money(COMPUTER_HOURLY)}")
    if eap["abbr"] != "FED":
        print(
            f"state EAP {eap['abbr']}/{eap['band']}: {money(state_w)}/week "
            f"({money(float(eap['annual']))}/year) — {eap['formula']}"
        )
        print(f"duties note: {eap['duties_note']}")
        print(f"controlling weekly floor = max(federal, state) = {money(floor)}")
        if eap.get("computer_hourly"):
            print(f"state computer hourly: {money(float(eap['computer_hourly']))}")
        if eap.get("computer_annual"):
            print(f"state computer annual: {money(float(eap['computer_annual']))}")
        if eap.get("hce_annual"):
            print(f"state HCE annual: {money(float(eap['hce_annual']))}")
        print(f"source: {eap.get('authority')}")
    else:
        print("no higher cited state EAP row — federal $684 controls the salary level.")
        print("controlling weekly floor = $684.00")
    if salary_weekly + 1e-9 < floor:
        print(
            f"RESULT: {money(salary_weekly)}/week is BELOW the controlling salary level "
            f"{money(floor)} — overtime exemption fails the salary test "
            "(duties test not evaluated)."
        )
    else:
        print(
            f"RESULT: {money(salary_weekly)}/week MEETS the controlling salary level "
            f"{money(floor)}. Duties test still required. Not advice."
        )
    if hourly is not None:
        ch = COMPUTER_HOURLY
        state_ch = float(eap["computer_hourly"]) if eap.get("computer_hourly") else None
        print(
            f"federal computer hourly compare: {money(hourly)} vs {money(ch)} → "
            + (
                "MEETS federal computer hourly"
                if hourly + 1e-9 >= ch
                else "BELOW federal computer hourly"
            )
        )
        if state_ch is not None:
            print(
                f"state computer hourly compare: {money(hourly)} vs {money(state_ch)} → "
                + (
                    "MEETS state computer hourly"
                    if hourly + 1e-9 >= state_ch
                    else "BELOW state computer hourly"
                )
            )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Overtime Floor Desk")
    p.add_argument("--list", nargs="?", const="ALL", help="list floors (optional state)")
    p.add_argument("--quote", help="state abbr to quote")
    p.add_argument("--hourly", type=float)
    p.add_argument("--hours", type=float, default=40.0)
    p.add_argument("--days", type=int, default=5)
    p.add_argument("--band", help="DOL-footnote band (downstate, portland, small, …)")
    p.add_argument("--daily", action="store_true", help="force daily-OT overlay")
    p.add_argument("--over-8", dest="over_8", type=float)
    p.add_argument("--over-12", dest="over_12", type=float)
    p.add_argument("--as-of", dest="as_of")
    p.add_argument("--batch")
    p.add_argument("--watch", action="store_true")
    p.add_argument("--cheap", action="store_true")
    p.add_argument("--high", action="store_true")
    p.add_argument("--bands", dest="show_bands")
    p.add_argument("--exempt", action="store_true")
    p.add_argument("--salary-weekly", dest="salary_weekly", type=float)
    p.add_argument("--state", help="state abbr for --exempt (uses higher of federal/state EAP)")
    p.add_argument("--list-eap", dest="list_eap", action="store_true")
    p.add_argument("--list-tips", dest="list_tips", nargs="?", const="ALL")
    p.add_argument("--tip", help="state abbr for tip-credit OT cash quote")
    p.add_argument("--role", help="tip role (food, service, hotel, bartender)")
    return p


def main() -> None:
    args = build_parser().parse_args()
    as_of = parse_as_of(args.as_of)
    if args.watch:
        cmd_watch()
        return
    if args.cheap:
        cmd_cheap()
        return
    if args.high:
        cmd_high()
        return
    if args.show_bands:
        cmd_bands(args.show_bands)
        return
    if args.list_eap:
        cmd_list_eap()
        return
    if args.list_tips:
        cmd_list_tips(None if args.list_tips == "ALL" else args.list_tips)
        return
    if args.tip:
        cmd_tip(args)
        return
    if args.exempt:
        if args.salary_weekly is None:
            raise SystemExit("--exempt needs --salary-weekly")
        cmd_exempt(args.salary_weekly, args.hourly, args.state or args.quote, args.band)
        return
    if args.batch:
        cmd_batch(Path(args.batch), bool(args.daily))
        return
    if args.list:
        cmd_list(None if args.list == "ALL" else args.list, as_of)
        return
    if args.quote:
        if args.hourly is None:
            raise SystemExit("--quote needs --hourly")
        cmd_quote(args)
        return
    build_parser().print_help()


if __name__ == "__main__":
    main()
