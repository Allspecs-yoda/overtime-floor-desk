# Sources

Cited figures only. Not wage-and-hour advice. Confirm with the named authority before you pay anyone.

## Federal

- **DOL WHD Consolidated Minimum Wage Table**, last revised **2026-07-01**, effective date on the table **July 1, 2026**. https://www.dol.gov/agencies/whd/mw-consolidated
  - Column 1 = greater than federal MW (30 states + DC, GU, PR, VI).
  - Column 2 = equals federal $7.25 (13 states + CNMI).
  - Column 3 = no state MW or state MW lower than $7.25 (AL, GA, LA, MS, SC, TN, WY + AS). FLSA $7.25 still applies to covered employers.
  - Footnotes used as written:
    - fn.3 Montana: non-FLSA employers with gross annual sales $110,000 or less may pay $4.00.
    - fn.4 New Jersey: fewer than 6 people and seasonal employment = **$15.23**; default ≥6 = **$15.92**.
    - fn.5 New York: NYC / Nassau / Suffolk / Westchester = **$17.00**; remainder = **$16.00**.
    - fn.6 Ohio: annual gross receipts under **$405,000** = **$7.25**; otherwise **$11.00**.
    - fn.7 Oregon: Portland metro **$16.80**; standard **$15.55**; nonurban **$14.55**.
- **FLSA §6(a)(1)** federal minimum wage **$7.25**/hour since 2009-07-24. 29 U.S.C. § 206(a)(1).
- **FLSA §7(a)** overtime: not less than one and one-half times the regular rate for hours over **40** in a workweek. 29 U.S.C. § 207(a).
- **DOL WHD EAP earnings thresholds**. https://www.dol.gov/agencies/whd/overtime/salary-levels
  - Standard salary level **$684**/week (**$35,568**/year).
  - Highly compensated employee **$107,432**/year including at least $684/week.
  - Computer employees paid hourly **$27.63**.
  - Special weekly levels: PR/GU/VI/CNMI **$455**; American Samoa **$380**; motion picture **$1,043**.
- **91 FR 27833** (published 2026-05-15): technical amendment implementing court judgments that vacated the 2024 Part 541 salary-level increases and restored the 2019 thresholds. DOL WHD announcement 2026-05-14.

## State EAP salary floors (2026) — higher than $684

`data/eap_state.csv` is a **secondary** overlay. `--exempt --state XX` uses `max(federal $684, cited state weekly)`. Not a duties test.

- **Washington** L&I overtime rules: 2026 salary threshold **$1,541.70**/week = **2.25 × $17.13 × 40** for both small (1–50) and large (51+) employers. Computer professionals **$59.96**/hour. https://www.lni.wa.gov/workers-rights/wages/overtime/changes-to-overtime-rules (WAC 296-128).
- **California** Lab. Code §515: EAP salary **twice** statewide MW for a 40-hour week → **2 × $16.90 × 40 = $1,352**/week (**$70,304**/year) as of 2026-01-01. No state HCE. Computer software employees Lab. Code §515.5 / DIR OPRL (Oct 2025 notice, effective 2026-01-01): **$58.85**/hour, **$10,214.44**/month, **$122,573.13**/year (3.3% CCPI). https://www.dir.ca.gov/oprl/ComputerSoftware.htm
- **New York** exec/admin salary (not professional): **$1,275.00**/week NYC + Nassau/Suffolk/Westchester; **$1,199.10**/week remainder, effective 2026-01-01. Professional exemption has **no NY salary** — federal $684 still applies. 12 NYCRR Part 142; NYS DOL 2026 wage orders.
- **Colorado** 2026 PAY CALC Order, 7 CCR 1103-14 (adopted 2025-12-08, published values for 2026): EAP **$1,111.23**/week (**$57,784** rounded annual) row E; highly technical computer **$34.85**/hour or the EAP weekly row F; HCE **$130,014** row G. https://www.sos.state.co.us/CCR/GenerateRulePdf.do?fileName=7+CCR+1103-14&ruleVersionId=12404
- **Alaska** AS 23.10.055(b): bona fide EAP “not less than **two times** the state minimum wage for the first 40 hours of employment each week.” DOL 2026-07-01 table lists AK MW **$14.00** (effective 2026-07-01) → **2 × $14 × 40 = $1,120**/week. https://ak.elaws.us/as/23.10.055
- **Maine** 26 M.R.S. §663(3)(K): salaried EAP whose regular compensation, annualized, exceeds **3000 times** the state MW **or** the federal annualized FLSA rate, whichever is higher. 3000 × $15.10 = **$45,300**/year → **$871.1538**/week, stored as **$871.16**. https://legislature.maine.gov/statutes/26/title26sec663.html

## State overlays used by the desk (not invented rates)

Statewide **dollar** rates in `min_wages.csv` come from the DOL 2026-07-01 table. Daily-OT flags are a **secondary** overlay, cited to the named statute, and only used when `--daily` is on or the state row’s `daily_ot` is not `flsa_40`:

- **California** Labor Code §510: 1.5× after 8 hours in a workday, 2× after 12, plus 40-hour week.
- **Alaska** AS 23.10.060: overtime after 8 hours in a day and 40 in a week.
- **Colorado** COMPS Order (CDLE): daily overtime after 12 hours in a workday in addition to 40-hour weekly OT.
- **Nevada** NRS 608.018: daily OT after 8 hours if the employee’s regular rate is less than 1.5× the applicable MW; otherwise weekly 40.
- **Florida** remaining Amendment 2 step: **$15.00** on **2026-09-30** (Fla. Const. Art. X §24 schedule). The DOL July 1 table still lists FL **$14.00**; `--as-of` switches the floor on 2026-09-30.

## What this desk does not invent

- Local city/county floors (Seattle, NYC fast food, LA hotel, etc.). DOL’s own footnote 1 says they are omitted from the consolidated table.
- Youth, training, or nonprofit subminimums.
- Tipped cash wages as a paid floor (tip-credit flag is informational only).
- Duties tests for the EAP exemption — salary is necessary, not sufficient.
- Local city EAP floors (Seattle, NYC, etc.).

Fetched 2026-08-27; state-EAP overlay added 2026-08-27T11:00Z.
