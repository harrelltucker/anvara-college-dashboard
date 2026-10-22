import json

import pandas as pd
import streamlit as st

from engine.data import load_findings
from engine.data import load_tables as load_tables_fresh
from engine.research import (WHERE_TO_LOOK, checklist, preview_finding, reject_finding,
                             submit_finding, verify_finding)
from engine.schema import TABLES
from engine.scoring import missing_inputs
from engine.validation import ERROR, issues_frame, run_checks
from ui import style
from ui.state import clear_cache, context

ctx = context()
scored, tables, weights = ctx["scored"], ctx["tables"], ctx["weights"]

style.hero("Research & data quality", "Every number is sourced and verified",
           "Only verified, sourced records affect scores. New findings, whether from a person or an AI research "
           "assistant, wait in a review queue until someone confirms the source.")

issues = issues_frame(run_checks(tables, weights["rules"]))
findings = load_findings()
pending = findings[findings["status"] == "pending"]

m = st.columns(5)
m[0].metric("Schools with complete FY2025 financials",
            f"{(scored['allocated_revenue'].notna() & scored['commercial_revenue'].notna()).sum()} / {len(scored)}")
m[1].metric("Verified rights relationships", len(tables["rights_relationships"]))
m[2].metric("Contacts identified", len(tables["contacts"]))
m[3].metric("Findings awaiting review", len(pending))
m[4].metric("Data issues", f"{(issues['severity'] == ERROR).sum()} errors · {(issues['severity'] != ERROR).sum()} warnings")

tabs = st.tabs(["Coverage", "Review queue", "Add a finding", "Research checklist",
                "Issues & conflicts", "Sources & licensing"])

with tabs[0]:
    status = tables["research_status"].pivot_table(index="school_id", columns="area", values="status", aggfunc="first")
    icons = {"complete": "✅ complete", "in_progress": "🟡 in progress", "not_started": "⬜ not started"}
    cov = status.reindex(scored.index).map(lambda v: icons.get(v, "⬜ not started"))
    cov.insert(0, "School", scored["name"])
    cov.insert(1, "FY25 financials", (scored["allocated_revenue"].notna() & scored["commercial_revenue"].notna())
               .map({True: "✅ complete", False: "⬜ missing"}))
    cov.insert(2, "Conference benchmark", scored.apply(
        lambda r: "✅" if pd.notna(r["conf_relative_generated"]) else f"⬜ {int(r['peer_count'])} peers", axis=1))
    cov["Completeness"] = scored["completeness"] * 100
    st.dataframe(cov, hide_index=True, width="stretch",
                 column_config={"Completeness": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%")})

with tabs[1]:
    if ctx["is_demo"]:
        st.info("The review queue works on research data only. Turn off demonstration data.")
    elif pending.empty:
        st.success("No findings awaiting review.")
    else:
        verifier = st.text_input("Your name (recorded as the verifier)", key="verifier")
        # One click for several findings backed by the same source (e.g., one partner page)
        for url, group in pending.groupby("source_url"):
            if len(group) < 2:
                continue
            blocked = [fid for fid, (_, f) in zip(group["finding_id"], group.iterrows())
                       if any(p.severity == ERROR for p in preview_finding(f, tables, verifier or "x")[2])]
            box = st.container(border=True)
            box.markdown(f"**{len(group)} findings from one source:** [{group['source_title'].iloc[0]}]({url})")
            if blocked:
                box.caption(f"{', '.join(blocked)} can't be verified yet (see errors below; often a "
                            "related record must be verified first).")
            if box.button(f"✅ I checked this source: verify all {len(group)}", key=f"bulk{url}",
                          disabled=not verifier or bool(blocked)):
                for fid in group["finding_id"]:
                    verify_finding(fid, load_tables_fresh(), verifier)
                clear_cache()
                st.rerun()
        kinds = sorted(pending["target_table"].unique())
        kind = st.selectbox("Review individual findings", kinds,
                            format_func=lambda k: f"{k.replace('_', ' ')} ({(pending['target_table'] == k).sum()})")
        shown = pending[pending["target_table"] == kind]
        if len(shown) > 40:
            st.caption(f"Showing the first 40 of {len(shown)}. Verify by source above to clear them faster.")
        for _, f in shown.head(40).iterrows():
            record, new_source, problems = preview_finding(f, tables, verifier or "(enter your name)")
            with st.expander(f"{f['finding_id']} · {f['target_table']} · {record.get('school_id', '')} · "
                             f"submitted by {f['submitted_by']} on {f['submitted_date']}"):
                st.markdown(f"**Source:** [{f['source_title']}]({f['source_url']})")
                st.json(record)
                for p in problems:
                    (st.error if p.severity == ERROR else st.warning)(p.message)
                st.caption("Open the source and confirm it supports every field before verifying.")
                a, b = st.columns(2)
                if a.button("✅ Verify & add to research data", key=f"v{f['finding_id']}",
                            disabled=not verifier or any(p.severity == ERROR for p in problems)):
                    errors = verify_finding(f["finding_id"], tables, verifier)
                    if errors:
                        st.error("; ".join(e.message for e in errors))
                    else:
                        clear_cache()
                        st.rerun()
                note = b.text_input("Rejection reason", key=f"n{f['finding_id']}")
                if b.button("Reject", key=f"r{f['finding_id']}", disabled=not note):
                    reject_finding(f["finding_id"], note)
                    st.rerun()
    done = findings[findings["status"] != "pending"]
    if len(done):
        st.markdown("**Reviewed findings**")
        st.dataframe(done[["finding_id", "target_table", "source_title", "submitted_by", "status", "review_note"]],
                     hide_index=True, width="stretch")

with tabs[2]:
    if ctx["is_demo"]:
        st.info("Turn off demonstration data to add research findings.")
    else:
        target = st.selectbox("What kind of finding?", ["financials", "audience", "catalysts",
                                                        "rights_relationships", "rights_holders", "contacts",
                                                        "market_context", "research_status"])
        spec = TABLES[target]
        skip = {"source_id", "verified_by", "verified_date"}
        with st.form("finding", clear_on_submit=True):
            record = {}
            cols = st.columns(2)
            for i, col in enumerate(c for c in spec["columns"] if c not in skip):
                box = cols[i % 2]
                label = col + (" *" if col in spec["required"] else "")
                if col in spec.get("enums", {}):
                    record[col] = box.selectbox(label, [""] + spec["enums"][col])
                elif col == "school_id":
                    record[col] = box.selectbox(label, [""] + list(tables["schools"]["school_id"]))
                else:
                    record[col] = box.text_input(label)
            st.markdown("**Source** (required)")
            s1, s2, s3 = st.columns([2, 2, 1])
            source_title = s1.text_input("Source title *")
            source_url = s2.text_input("Source URL *")
            source_type = s3.selectbox("Source type", TABLES["sources"]["enums"]["source_type"][:-1])
            submitted_by = st.text_input("Submitted by", value="Tucker")
            if st.form_submit_button("Submit for review"):
                if not source_title or not source_url.startswith(("http://", "https://")):
                    st.error("A source title and a full web link are required.")
                else:
                    fid = submit_finding(target, {k: v.strip() for k, v in record.items()},
                                         source_title, source_url, source_type, submitted_by)
                    st.success(f"{fid} added to the review queue. It won't affect scores until verified.")

with tabs[3]:
    school = st.selectbox("School", list(scored.index), format_func=lambda s: scored.loc[s, "name"])
    row = scored.loc[school]
    st.dataframe(checklist(school, row, tables, missing_inputs(row, tables)), hide_index=True, width="stretch")
    with st.expander("Where each kind of data comes from"):
        for area, where in WHERE_TO_LOOK.items():
            st.markdown(f"- **{area}**: {where}")

with tabs[4]:
    if issues.empty:
        st.success("All checks pass.")
    else:
        st.dataframe(issues, hide_index=True, width="stretch")
    st.caption("Conflicting values for the same school and year appear here as errors, never silently resolved.")

with tabs[5]:
    src = tables["sources"]
    if src.empty:
        st.info("No sources recorded yet.")
    else:
        st.dataframe(src, hide_index=True, width="stretch", column_config={"url": st.column_config.LinkColumn()})
    st.markdown("""
**Licensing.** Primary public documents (university NCAA financial reports, state transparency
portals, official releases, NCAA statistics) are preferred. Where a school's own report isn't
public, FY2025 figures come from the Knight–Newhouse College Athletics Database, which is free for
non-commercial use with credit. It is credited on every page, raw downloads are not redistributed,
and its figures are blanked in CSV exports (*export_allowed = no*). Commercial use needs Knight–Newhouse's
permission.
""")
