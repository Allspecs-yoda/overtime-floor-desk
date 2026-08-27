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

FL_STEP_ON = date(2026, 9, 30)
FL_STEP_RATE = 15.00
EAP_WEEKLY = 684.0
EAP_ANNUAL = 35568.0
HCE_ANNUAL = 107432.0
COMPUTER_HOURLY = 27.63
OT_MULT = 1.5
WEEKLY_OT_HOURS = 40.0
FED_MW = 7.25


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


def parse_as_of(s: str | None) -> date:
    if not s:
        return datetime.now().date()
    return datetime.strptime(s, "%Y-%m-%d").date()


def money(n: float) -> str:
    return f"${n:,.2f}"


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
                exempt = "BELOW_EAP" if sw < EAP_WEEKLY else "MEETS_EAP_SALARY"
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
    print("- Highest DOL July 1 statewide listed: DC $18.40; next WA $17.13.")
    print("- NY split: downstate $17.00 / rest $16.00 (DOL fn.5).")
    print("- OR split: Portland $16.80 / standard $15.55 / nonurban $14.55 (DOL fn.7).")
    print("- NJ split: ≥6 employees $15.92 / <6 or seasonal $15.23 (DOL fn.4).")
    print("- OH small-employer $7.25 if gross receipts under $405,000 (DOL fn.6).")


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


def cmd_exempt(salary_weekly: float, hourly: float | None) -> None:
    print(f"EAP weekly salary test: {money(EAP_WEEKLY)}  (annual {money(EAP_ANNUAL)})")
    print(f"HCE annual: {money(HCE_ANNUAL)}")
    print(f"computer hourly: {money(COMPUTER_HOURLY)}")
    if salary_weekly < EAP_WEEKLY:
        print(
            f"RESULT: {money(salary_weekly)}/week is BELOW the EAP salary level — "
            "overtime exemption fails the salary test (duties test not evaluated)."
        )
    else:
        print(
            f"RESULT: {money(salary_weekly)}/week MEETS the EAP salary level. "
            "Duties test still required. Not advice."
        )
    if hourly is not None:
        print(
            f"computer hourly compare: {money(hourly)} vs {money(COMPUTER_HOURLY)} → "
            + (
                "MEETS computer hourly"
                if hourly + 1e-9 >= COMPUTER_HOURLY
                else "BELOW computer hourly"
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
    if args.exempt:
        if args.salary_weekly is None:
            raise SystemExit("--exempt needs --salary-weekly")
        cmd_exempt(args.salary_weekly, args.hourly)
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
