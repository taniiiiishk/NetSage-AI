"""NetSage AI Streamlit UI. It never connects to equipment."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from src.audit import record, summary
from src.engine import diagnose
from src.remediation import as_text
ROOT=Path(__file__).resolve().parent
def load_data():
    try:
        cases=pd.read_csv(ROOT/"data"/"cases.csv").fillna("")
        required={"case_id","symptom","topology_note","concept_tag","severity","show_outputs","expected_fault"}
        if not required.issubset(cases.columns): raise ValueError("cases.csv is missing required columns")
        config=json.loads((ROOT/"data"/"system_config.json").read_text())
        return cases,config,None
    except (OSError,ValueError,json.JSONDecodeError,pd.errors.ParserError) as exc: return pd.DataFrame(),{},str(exc)
st.set_page_config(page_title="NetSage AI",page_icon="🛡️",layout="wide")
st.title("NetSage AI: Automated Network Diagnostic Platform")
st.caption("Educational Cisco Packet Tracer diagnostics • recommendations only • SIMULATED DEPLOYMENT")
cases,config,error=load_data()
if error: st.error(f"Could not load project data: {error}"); st.stop()
st.sidebar.header("Operations")
case_id=st.sidebar.selectbox("Case selector",cases["case_id"].tolist())
case=cases.loc[cases.case_id==case_id].iloc[0].to_dict()
st.subheader(f"{case_id} — {case['symptom']}")
a,b,c=st.columns(3); a.metric("Concept",case["concept_tag"]); b.metric("Severity",case["severity"]); c.metric("Mode","SIMULATION ONLY")
st.write("**Topology:**",case["topology_note"]); st.code(case["show_outputs"],language="text")
if st.button("Run Diagnosis",type="primary"):
    st.session_state.result=diagnose(case,config); st.session_state.active_case=case_id
result=st.session_state.get("result") if st.session_state.get("active_case")==case_id else None
if result:
    st.subheader("Diagnostic result")
    st.write("Source:",result["source"]); st.json(result["checker_results"])
    d=result["diagnosis"]; x,y,z=st.columns(3); x.metric("Root cause",d["root_cause"]); y.metric("OSI layer",d["osi_layer"]); z.metric("Confidence",f"{d['confidence']:.0%}")
    st.write("**Evidence:**",d["evidence"]); st.write("**Next diagnostic command:**",d["next_command"]); st.write("**Recommended fix steps:**",d["fix_steps"])
    edited=st.text_area("Recommendation-only Cisco commands",as_text(result["recommended_commands"]),key=f"cmd_{case_id}")
    st.warning("Human approval is required. This app will only record a simulated deployment; it never connects to devices.")
    p,q,r=st.columns(3)
    if p.button("Approve & Deploy Fix"):
        record(case_id,d,result["checker_results"],"approved",deployment_status="simulated_completed"); st.success("Fix approved — simulated deployment completed. (SIMULATED DEPLOYMENT)")
    if q.button("Edit Commands"):
        record(case_id,d,result["checker_results"],"edited",override=True); st.info("Edited recommendation recorded. No commands were executed.")
    if r.button("Reject"):
        record(case_id,d,result["checker_results"],"rejected",override=True); st.info("Rejection / false-positive event recorded.")
st.sidebar.subheader("Audit summary")
try:
    events=json.loads((ROOT/"data"/"audit_events.json").read_text())
except (OSError,json.JSONDecodeError): events=[]
st.sidebar.json(summary(events))
