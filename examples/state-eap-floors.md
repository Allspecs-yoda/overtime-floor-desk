# Federal $684 is not enough in six states

A $900/week “manager” salary clears the restored federal EAP test ($684) and still fails California, Washington, New York (exec/admin), Colorado, and Alaska. Maine’s 3,000× MW floor is $871.16 — $900 scrapes by there.

```bash
python3 desk/quote.py --list-eap
python3 desk/quote.py --exempt --salary-weekly 900 --state CA
python3 desk/quote.py --exempt --salary-weekly 900 --state WA
python3 desk/quote.py --exempt --salary-weekly 900 --state NY --band downstate
python3 desk/quote.py --exempt --salary-weekly 900 --state CO
python3 desk/quote.py --exempt --salary-weekly 900 --state AK
python3 desk/quote.py --exempt --salary-weekly 900 --state ME
python3 desk/quote.py --exempt --salary-weekly 900 --state TX
python3 desk/quote.py --exempt --salary-weekly 650 --hourly 30 --state CA
```

Cited 2026 weekly floors (not invented):

| where | weekly | formula |
| --- | ---: | --- |
| Federal | $684.00 | 29 C.F.R. Part 541 / 91 FR 27833 |
| WA | $1,541.70 | 2.25 × $17.13 × 40 (L&I 2026) |
| CA | $1,352.00 | 2 × $16.90 × 40 (Lab. Code §515) |
| NY downstate | $1,275.00 | NYC / Nassau / Suffolk / Westchester exec/admin |
| NY rest | $1,199.10 | remainder exec/admin |
| AK | $1,120.00 | AS 23.10.055(b) 2 × $14.00 × 40 (after 2026-07-01) |
| CO | $1,111.23 | 7 CCR 1103-14 PAY CALC row E |
| ME | $871.16 | 26 M.R.S. §663(3)(K) 3000 × $15.10 |

CA computer software (Lab. Code §515.5 / DIR OPRL): **$58.85/hr** or **$122,573.13/yr** as of 2026-01-01. WA computer **$59.96/hr**. CO computer **$34.85/hr** or the EAP weekly; CO HCE **$130,014**. California has no state HCE.

Duties tests are not evaluated. Not wage-and-hour advice.
