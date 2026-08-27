# Nevada daily OT only if the rate is cheap

NRS 608.018: 1.5× after 8 hours in a day **if** the regular rate is less than 1.5× the applicable MW. Otherwise weekly 40 only.

NV floor on DOL 2026-07-01: $12.00. 1.5× MW = $18.00.

```bash
python3 desk/quote.py --quote NV --hourly 12 --hours 45 --days 5 --daily
python3 desk/quote.py --quote NV --hourly 20 --hours 45 --days 5 --daily
```

$12/hour (at floor) picks up daily OT. $20/hour does not.

Not wage-and-hour advice.
