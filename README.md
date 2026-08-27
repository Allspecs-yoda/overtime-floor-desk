# Overtime Floor Desk

Offline 2026 desk that prices a shift against **51 min-wage floors** (50 states + DC) from the **DOL WHD Consolidated Minimum Wage Table (revised 2026-07-01)**, FLSA **1.5× after 40**, the restored EAP salary test (**$684/week / $35,568** after the 2024 rule was vacated), and cited daily-OT overlays (CA §510 after 8/12, AK after 8, CO after 12, NV after 8 only if the rate is cheap). Florida’s remaining **$15.00 on 2026-09-30** step is an `--as-of` switch — the July table still lists $14.00.

## Who it's for

Owners, bookkeepers, and ops leads who still quote OT off a $7.25 blog post, miss NY/OR/NJ/OH footnote bands, or think the 2024 white-collar salary hike is live.

## What's included

- `data/min_wages.csv` — 51 rows: DOL July 1, 2026 statewide floor, daily-OT flag, next step
- `data/bands.csv` — NY downstate $17 / rest $16; OR Portland $16.80 / standard $15.55 / nonurban $14.55; NJ $15.92 / $15.23; OH $11 / $7.25
- `data/flsa.csv` — $7.25, 40-hour week, EAP $684 / HCE $107,432 / computer $27.63
- `data/sample_shifts.csv` — 13 worked quotes (CA 9×5, FL step, NV gate, EAP miss)
- `desk/quote.py` — `--list`, `--quote`, `--batch`, `--watch`, `--cheap`, `--high`, `--bands`, `--exempt`, `--as-of`
- `examples/` — CA daily OT, FL $15 step, NY/OR bands, EAP $684, NV daily gate
- `data/SOURCES.md` — DOL WHD table, 29 U.S.C. §§ 206–207, 91 FR 27833, named state statutes

## Quick start

```bash
python3 desk/quote.py --watch
python3 desk/quote.py --list CA
python3 desk/quote.py --quote TX --hourly 18 --hours 48
python3 desk/quote.py --quote CA --hourly 22 --hours 45 --days 5 --daily
python3 desk/quote.py --quote NY --hourly 16.50 --hours 40 --band downstate
python3 desk/quote.py --quote FL --hourly 14 --hours 40 --as-of 2026-09-30
python3 desk/quote.py --quote NV --hourly 12 --hours 45 --days 5 --daily
python3 desk/quote.py --exempt --salary-weekly 650
python3 desk/quote.py --batch data/sample_shifts.csv
python3 desk/quote.py --cheap
python3 desk/quote.py --high
python3 desk/quote.py --bands OR
```

No API keys. Files work after Gamut credits are gone. Not wage-and-hour advice. Confirm with the named DOL / state labor office before you pay anyone.

## Price

$49 USD. Unlimited non-exclusive buyers; copies may be resold. Payments are not connected on this cycle — star + watch, then open a GitHub issue titled `CLAIM: Overtime Floor Desk`. If a Payment Link is added later, put the receipt last-4 in that issue.

## License

MIT for the desk code, CSVs, and docs. Cited DOL / FLSA / state figures remain their works. See LICENSE.

## Foundry

Shipped by Night Shift Foundry for Dakota (@Allspecs-yoda).
SKU: NSF-20260827-OT-FLOOR | Decision: list | Cycle: 2026-08-27
