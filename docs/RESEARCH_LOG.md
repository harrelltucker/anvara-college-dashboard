# Research log

Decisions, findings and open questions. Source material for the Anvara presentation.

## Decisions (2026-10-22)
- Pivoted from the PE-ownership tracker (`../sports-pe-tracker`) to a college-athletics sponsorship-opportunity model. Carried over: source/verification discipline, Utah–Otro research, Learfield partner list.
- Conference benchmarks need FY2025 financials for all members of Big Ten, Big 12, SEC and ACC (~60 schools), collected as benchmark-only peers. Until coverage reaches 50% of a conference, the component is left out rather than using a partial sample.
- Reported surplus/deficit kept as specified (scored as % of expenses). Phase 3 will check whether it varies enough across schools to be meaningful, since subsidies often bring reported results near zero.
- Normalization: percentile ranks within the school universe (outlier-proof); catalysts use a fixed rubric.
- Knight–Newhouse database used only for definitions and cross-checks (license terms unconfirmed); primary NCAA reports are the source of record.
- Research carried over from the earlier project was queued as **pending findings** rather than loaded directly, so it goes through the same human verification as new research.

## Open questions
- Is the TPG acquisition of Learfield closed? (Expected Q3 2026.)
- Which Learfield services apply to each partner school? The partner page doesn't say.
- Would Knight–Newhouse permit portfolio use of their data? (Worth asking.)

## Knight–Newhouse (2026-10-22)
- Terms read: free for non-commercial use with credit; copyright protected; no commercial use or redistribution without permission. Treated as non-commercial portfolio use: credited, `export_allowed = no`, raw downloads kept out of Git (`data/incoming/`). Commercial use by Anvara would need permission (contact listed in their terms).
- Cross-check vs. original NCAA reports: Illinois and Wisconsin match exactly (revenue, expenses, sponsorship line). Ohio State matches on revenue and sponsorship, but K-N expenses are $320,661,665 vs. $320,394,965 in OSU's own report ($266,700 higher). Original reports win where available.
- First download lacked student fees and combines institutional/government support **before** transfers to the institution (total revenue is after transfers), so generated revenue can't be computed consistently from it. Re-download requested with the separate lines.
- K-N covers public schools only. Peer coverage for FY2025: Big Ten 16 of 18 members, SEC 15/16, Big 12 13/16, **ACC 9/18**, so Clemson's conference benchmark (8 of 17 peers, 47%) falls just under the 50% rule. Decision pending.
