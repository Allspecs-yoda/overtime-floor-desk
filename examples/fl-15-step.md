# Florida $15 step on 2026-09-30

DOL’s July 1, 2026 table still lists Florida at **$14.00**. Fla. Const. Art. X §24’s remaining Amendment 2 step is **$15.00 on 2026-09-30**.

```bash
python3 desk/quote.py --quote FL --hourly 14 --hours 40 --as-of 2026-09-29
python3 desk/quote.py --quote FL --hourly 14 --hours 40 --as-of 2026-09-30
```

Pre-step: AT_FLOOR $14.00. Post-step: UNDER_FLOOR against $15.00. `--watch` prints the same date.

Not wage-and-hour advice.
