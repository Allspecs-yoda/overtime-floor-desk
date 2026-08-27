# Tip credit does not freeze OT cash at $2.13

Federal cash wage for a tipped hour is still **$2.13**, but overtime cash is **$5.76** = 1.5 × $7.25 − $5.12 (29 CFR 531.60). Excess tips are not in the regular rate.

```bash
python3 desk/quote.py --list-tips TX
python3 desk/quote.py --tip TX --hours 48
python3 desk/quote.py --tip CA --hours 48
python3 desk/quote.py --tip NY --band downstate --role food --hours 45
python3 desk/quote.py --tip NY --band rest_of_state --role service --hours 44
python3 desk/quote.py --tip CT --role bartender --hours 42
python3 desk/quote.py --list-tips
```

Worked federal 48-hour week (TX / FLSA cash):

| bucket | hours | cash rate | employer cash |
| --- | ---: | ---: | ---: |
| Straight | 40 | $2.13 | $85.20 |
| OT | 8 | $5.76 | $46.08 |
| **Employer cash** | 48 | | **$131.28** |

Worked NYC food-service 45-hour week (NY DOL 2026-01-01):

| bucket | hours | cash rate | employer cash |
| --- | ---: | ---: | ---: |
| Straight | 40 | $11.35 | $454.00 |
| OT | 5 | $19.85 (= 1.5×$17.00 − $5.65) | $99.25 |
| **Employer cash** | 45 | | **$553.25** |

California has **no** tip credit: 48 hours at $16.90 cash OT at $25.35. Not wage-and-hour advice.
