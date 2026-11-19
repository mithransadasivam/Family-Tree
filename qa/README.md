# Kinship QA

One command runs every check and prints a summary. It is safe to run as often as you like: the
server checks use a throwaway in-memory database, the website checks are pure code, and the
optional `--live` checks only read from the real site.

```
python qa/run_all.py              everything (about a minute)
python qa/run_all.py --quick      fewer random rounds (about 20 seconds)
python qa/run_all.py --live       also poke the live website (read-only)
python qa/run_all.py --seed 123   replay the exact random run another run printed
```

On Windows you can also double-click `qa/run_qa.bat`.

## What it covers

| Group | What it does |
|---|---|
| access control | people can't reach other families' data, move people between families, link accounts they shouldn't, delete without being the owner; deleted families stay gone; relationship rules; dates |
| communities | create, join, approve, share families, search and filters, privacy of what members see |
| emails | the join-request emails and approve links (using a fake mailbox) |
| join with family | pick a family when joining a community; shared on approval |
| private details | the eye buttons: email, phone and address stay hidden unless turned on |
| random fuzz | thousands of random, often nonsensical, requests from several users, while checking that the server never errors, links never cross families / double up / loop, private values never leak, strangers stay locked out |
| website tests | the tree layout and labels, including random families shuffled in every order |
| live site (`--live`) | the real site loads, both addresses match, and every private page turns anonymous visitors away |

Every random run prints its seed. If a run fails, re-run with that seed to see the same failure.

Add a new check by dropping a script in `qa/scenarios/` named `check_<something>.py`: print
`PASS ...` or `FAIL ...` lines and exit non-zero on failure (see an existing one for the setup).
