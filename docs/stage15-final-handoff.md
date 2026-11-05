# Stage 15 — Final submission and quick demo

This stage collects the final Persian 10-page technical report (editable DOCX and PDF) and one comprehensive copy-ready PowerShell TXT runbook. It does not introduce a new banking algorithm.

## Critical verified observation from the student's Stage14 run

`verify_stage14 --scenario=postcutover --json` currently FAILS against the student's database because `shard_map` still has A:1–1000 and B:1001–2000, with no C ownership. This is a **pre-cutover state**, not a post-cutover success. Never edit shard_map directly or claim Stage14 acceptance passed.

1. Run `python -m scripts.verify_stage12 --scenario=preflight` in `schema-migrator`.
2. If not ready, inspect `migration_jobs`, build the consistent Stage10 snapshot and Stage11 C shadow replay as needed, then rerun preflight.
3. After durable 2PC checks and a DB backup, execute **the one-way** Stage12 cutover once.
4. Run `verify_stage12 --scenario=stale` and `--scenario=recovered`, then `backfill_stage13` and `verify_stage13 --scenario=preflight`.
5. Only now rerun `verify_stage14 --scenario=postcutover --json` and the rest of Stage13 postcutover tests.

See `stage15-all-tests-powershell.txt` for grouped commands and the full matrix of old vs. new state tests. Do not run all commands as a single script, because tests are mutually exclusive across cutover boundaries and some deliberately kill services.

## Submission checklist

- [ ] All 7 mandatory experiments have **real Docker evidence**.
- [ ] Stage07 coordinator kill after durable COMMIT and Stage09 controller crash recovery are demonstrated.
- [ ] Bonus I snapshot / live journal replay / stale fencing / all four Stage14 crash points verified on isolated labs.
- [ ] Bonus II new container ID + monotonically increasing generation + no duplicate active slot verified.
- [ ] Technical report has been filled with real Github and Docker Hub URLs, name, and observed test results; DOCX/PDF are exactly 10 pages A4.
- [ ] Complete source pushed to Github, Docker Hub image(s) pushed, the video is ≤15 minutes.
- [ ] Secrets `.env` and database contents are not committed.

## Git and Docker Hub

```powershell
git status
git diff --check
git ls-files .env
git add .
git commit -m "docs: final Persian technical report and demo checklist"
git push origin main
# Create stage-15 tag only after acceptance passes and only if absent.
# Replace Docker Hub username with actual account before these commands.
docker login
docker tag distributed-banking-app:stage14 YOUR_DOCKERHUB_USER/distributed-banking-app:stage15
docker push YOUR_DOCKERHUB_USER/distributed-banking-app:stage15
```

No `docker compose down -v` or manual SQL balance repair. Save request IDs for ambiguous outcomes.
