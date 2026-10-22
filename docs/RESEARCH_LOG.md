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

## Attendance and growth catalysts (2026-10-22)
Queued as findings F-0071 to F-0140 (70 findings); nothing is scored until verified.

**Attendance (2024-25 = FY2025)**
- Football: NCAA's official 2024-season attendance table (all FBS schools). The live NCAA file now shows only 2025, so the archived copy (Wayback Machine, 2025-10-30) is the source. Ohio State (9 games) and Texas (8) include College Football Playoff home games, as counted by the NCAA.
- Basketball: each school's official 2024-25 cumulative statistics, home games only. UCLA, Arizona State and Purdue load stats from an embedded WMT feed (NCAA data). Spot checks: Texas women 7,836 matches Texas's own release; Wisconsin men 15,006 matches other reporting; Purdue men 14,876 = Mackey Arena capacity, consistent with announced sellouts of every home game.
- **Gap:** Clemson and Iowa basketball. Their stats pages don't expose 2024-25 figures, and news gives only approximations (Iowa men "just over 9,000" per KCRG; listed vs. scanned tickets differ widely per The Gazette). Left missing; fan reach for those two uses football only, and confidence drops to Medium.
- The NCAA's own 2024-25 basketball attendance reports weren't reachable (no public copy found).

**Growth catalysts (scan of Oct 2024 to Oct 2026; rubric in METHODOLOGY)**
Rating guide used for consistency: *high* = new commercial company, in-house rights takeover or private capital; *medium* = senior commercial hire, restructured rights deal, new inventory class (jersey patch, on-field logo), naming rights; *low* = a single sponsorship or small new revenue product. NIL-facing and facility items are marked *indirect*.
- In-house/commercial entities: Rutgers (SAMCO 2024 → Scarlet Knight Enterprises 2026, CEO Fred Mangione), Clemson (Clemson Ventures 2024, CEO Michael Drake 2025), Michigan State (Spartan Ventures + for-profit Spartan Media Ventures built for capital investment, July 2026), Arizona (Arizona Sports Enterprises 2024), Utah (Otro Capital, already queued).
- New inventory: jersey patches (MSU–MSUFCU, Ohio State–JPMorganChase, Illinois–Busey), on-field logos (Iowa–John Deere, Purdue–Progressive, Illinois–Caterpillar). The NCAA allowed patches from Aug. 1, 2026; a school's own deal counts, the rule itself doesn't.
- Other: Ohio State–Learfield restructured extension; Arizona stadium and arena naming rights; UCLA's new CEO/AD with a revenue mandate; Wisconsin NIL unit; Texas–Huntington; Maryland fan tokens; ASU arena renovation plan.
- Minnesota: no qualifying event found (a raffle and no jersey-patch sponsor yet), so it's a researched 0.

**Corrections**
- Rejected F-0003 (Arizona–Learfield) and F-0009 (Rutgers–Learfield): both schools moved multimedia rights in-house in 2024, with Learfield kept for national sales. Replaced with in-house rights findings. **Anvara angle:** in-house schools sell their own inventory and may be direct marketplace customers; Learfield schools go through the rights holder.

**Not scored, but notable for the deck**
- Big 12's RedBird/Weatherford deal offers each school a $30M credit line; Arizona declined, ASU and Utah undisclosed (May 2026).
- Big Ten's proposed $2.4B UC Investments deal ("Big Ten Enterprises") is paused. It's a scenario, not a catalyst.
- Wisconsin gets $14.6M/yr in state debt-service support (2026 law). That's financial support, not a commercial catalyst.

**Verification order:** rights holders (F-0001, F-0002, F-0133/135/137/139) before their relationships; then the rest in any order.
