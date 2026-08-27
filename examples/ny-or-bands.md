# NY / OR / NJ / OH DOL footnote bands

The consolidated table prints split rates. Default `--list` uses the statewide/rest-of-state row; `--band` switches.

```bash
python3 desk/quote.py --bands NY
python3 desk/quote.py --quote NY --hourly 16.50 --hours 40 --band rest_of_state
python3 desk/quote.py --quote NY --hourly 16.50 --hours 40 --band downstate
python3 desk/quote.py --bands OR
python3 desk/quote.py --quote OR --hourly 15.55 --hours 40 --band portland
python3 desk/quote.py --bands NJ
python3 desk/quote.py --bands OH
```

NYC/Nassau/Suffolk/Westchester $17.00 vs remainder $16.00 (fn.5). Portland metro $16.80 vs standard $15.55 vs nonurban $14.55 (fn.7). NJ <6 or seasonal $15.23 vs $15.92 (fn.4). OH gross receipts under $405k → $7.25 (fn.6).

Not wage-and-hour advice.
