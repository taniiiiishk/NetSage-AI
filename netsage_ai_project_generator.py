
from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

FILES: dict[str, str] = {
"requirements.txt": '''streamlit>=1.31\npandas>=2.0\npython-dotenv>=1.0\n''',
".env.example": '''# Optional. Without this key, NetSage uses its safe mock LLM.\nOPENAI_API_KEY=\nOPENAI_MODEL=gpt-4o-mini\n''',
".gitignore": '''.env\n__pycache__/\n.pytest_cache/\ndata/audit_events.json\n''',
"src/__init__.py": '''\"\"\"NetSage AI package: offline, simulated network diagnosis only.\"\"\"\n''',
"data/system_config.json": '''{
  "confidence_threshold": 0.7,
  "llm_enabled": true,
  "mock_mode": true,
  "model_name": "gpt-4o-mini",
  "human_approval_required": true,
  "simulation_mode": true,
  "audit_logging": true
}\n''',
"src/checker.py": r'''"""Deterministic, evidence-only checks for simulated Cisco outputs."""
from __future__ import annotations
import re
from typing import Any

RULES = [
 ("administratively_down", r"(?im)^\s*(\S+)\s+is administratively down,\s*line protocol is down", "Interface {interface} is administratively down."),
 ("line_protocol_down", r"(?im)^\s*(\S+)\s+is up,\s*line protocol is down", "Interface {interface} has an up/down line protocol."),
 ("vlan_mismatch", r"(?i)(?:native vlan mismatch|vlan mismatch|inconsistent vlan)", "A VLAN mismatch is reported."),
 ("missing_vlan", r"(?i)(?:vlan\s+\d+\s+(?:does not exist|not found)|%.*vlan.*not.*exist)", "A required VLAN is missing."),
 ("trunk_problem", r"(?i)(?:trunking.*not|operational mode.*not trunk|nonegotiate.*mismatch)", "A trunk configuration problem is reported."),
 ("encapsulation_mismatch", r"(?i)(?:encapsulation.*mismatch|encapsulation.*not configured|dot1q.*mismatch)", "An encapsulation mismatch is reported."),
 ("ip_configuration", r"(?i)(?:duplicate address|invalid mask|overlaps with|wrong subnet)", "An IP addressing problem is reported."),
 ("acl_deny", r"(?i)(?:access-list.*deny|acl.*deny|denied by.*access)", "Traffic is denied by an ACL."),
 ("dhcp_problem", r"(?i)(?:dhcp.*(?:failed|no address|unable)|no dhcp offers)", "DHCP allocation is failing."),
 ("dns_problem", r"(?i)(?:unknown host|dns.*(?:fail|unreachable)|name lookup.*fail)", "DNS resolution is failing."),
]

def check(show_output: str) -> list[dict[str, Any]]:
    """Return all observed rule matches; never infer facts not in the output."""
    if not isinstance(show_output, str) or not show_output.strip():
        return [{"rule":"empty_output","detected":False,"message":"No show output supplied.","evidence":"","confidence":0.0}]
    results=[]
    for name, pattern, message in RULES:
        match=re.search(pattern, show_output)
        if match:
            evidence=match.group(0).strip()
            interface=match.group(1) if match.lastindex else "the interface"
            results.append({"rule":name,"detected":True,"message":message.format(interface=interface),"evidence":evidence,"confidence":0.98 if name=="administratively_down" else 0.9})
    return results or [{"rule":"no_known_rule","detected":False,"message":"No deterministic signature matched.","evidence":"","confidence":0.0}]
''',
"src/parser.py": r'''"""Validation for structured diagnostic responses."""
from __future__ import annotations
import json
from typing import Any
REQUIRED={"case_id":str,"root_cause":str,"osi_layer":str,"confidence":(int,float),"evidence":list,"next_command":str,"fix_steps":list,"severity":str,"requires_human_approval":bool}
def validate_diagnosis(payload: Any) -> dict[str, Any]:
    if isinstance(payload,str):
        try: payload=json.loads(payload)
        except json.JSONDecodeError as exc: raise ValueError("LLM response is not valid JSON") from exc
    if not isinstance(payload,dict): raise ValueError("Diagnostic result must be a JSON object")
    missing=set(REQUIRED)-set(payload)
    if missing: raise ValueError(f"Missing diagnostic fields: {', '.join(sorted(missing))}")
    for key, expected in REQUIRED.items():
        if not isinstance(payload[key],expected): raise ValueError(f"Invalid type for {key}")
    confidence=float(payload["confidence"])
    if not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
    payload["confidence"]=confidence
    payload["requires_human_approval"]=True  # immutable safety guard
    return payload
''',
"src/remediation.py": r'''"""Recommendation-only IOS snippets. These strings are never executed."""
from __future__ import annotations
from typing import Iterable
def commands_for(rule: str, evidence: str="") -> list[str]:
    interface="GigabitEthernet0/0.30"
    if evidence: interface=evidence.split()[0]
    mapping={
      "administratively_down":["configure terminal",f"interface {interface}","no shutdown"],
      "line_protocol_down":["show interfaces", "show running-config interface <interface>"],
      "vlan_mismatch":["show interfaces trunk", "show vlan brief", "configure terminal", "interface <trunk-interface>", "switchport trunk native vlan <expected-vlan>"],
      "missing_vlan":["configure terminal", "vlan <vlan-id>", "name <vlan-name>"],
      "trunk_problem":["configure terminal", "interface <trunk-interface>", "switchport mode trunk"],
      "encapsulation_mismatch":["configure terminal", "interface <sub-interface>", "encapsulation dot1Q <vlan-id>"],
      "acl_deny":["show access-lists", "configure terminal", "ip access-list extended <acl-name>", "no deny <matching-rule>"],
    }
    return mapping.get(rule,["show running-config", "show ip interface brief", "Review configuration against the documented topology."])
def as_text(commands: Iterable[str])->str: return "\n".join(commands)
''',
"src/llm.py": r'''"""Optional LLM adapter; mock mode is the safe default and never executes commands."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
def _mock(case:dict[str,Any], mode:str, note:str="")->dict[str,Any]:
    return {"case_id":str(case.get("case_id","UNKNOWN")),"root_cause":"No deterministic signature found; inspect the supplied output and topology.","osi_layer":"Unknown","confidence":0.35,"evidence":["No supported deterministic signature was found."],"next_command":"show running-config","fix_steps":["Collect the suggested show command output.","Have a human review any recommendation before simulation."],"severity":str(case.get("severity","medium")),"requires_human_approval":True,"analysis_mode":mode,"note":note}
def analyze(case:dict[str,Any], show_output:str, config:dict[str,Any])->dict[str,Any]:
    """Call the optional Responses API only when mock mode is explicitly disabled."""
    key=os.getenv("OPENAI_API_KEY")
    if config.get("mock_mode",True) or not config.get("llm_enabled",True) or not key: return _mock(case,"mock")
    try:
        prompt=(ROOT/"prompts"/"diagnose_prompt.md").read_text(encoding="utf-8")
        body={"model":config.get("model_name","gpt-4o-mini"),"input":[{"role":"system","content":prompt},{"role":"user","content":f"Case: {json.dumps(case)}\\nShow output:\\n{show_output}"}],"text":{"format":{"type":"json_object"}}}
        req=Request("https://api.openai.com/v1/responses",data=json.dumps(body).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},method="POST")
        with urlopen(req,timeout=20) as response: result=json.loads(json.loads(response.read()).get("output_text",""))
        result["analysis_mode"]="openai"; return result
    except Exception as exc: return _mock(case,"mock_fallback",f"Optional LLM unavailable: {type(exc).__name__}")
''',
"src/audit.py": r'''"""Local audit trail for decisions and explicitly simulated deployments."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
EVENTS=ROOT/"data"/"audit_events.json"; REPORT=ROOT/"docs"/"model_audit_log.md"
def _load()->list[dict[str,Any]]:
    try:
        value=json.loads(EVENTS.read_text())
        return value if isinstance(value,list) else []
    except (OSError,json.JSONDecodeError): return []
def summary(events:list[dict[str,Any]])->dict[str,int|float]:
    total=len(events); approved=sum(e["human_decision"]=="approved" for e in events); rejected=sum(e["human_decision"]=="rejected" for e in events); edited=sum(e["human_decision"]=="edited" for e in events)
    overrides=sum(bool(e.get("override")) for e in events); deployments=sum(e.get("deployment_status")=="simulated_completed" for e in events)
    agreement=round(100*(approved/max(1,approved+rejected)),1)
    return {"total_diagnoses":total,"approved_cases":approved,"rejected_cases":rejected,"edited_cases":edited,"human_overrides":overrides,"false_positives":rejected,"simulated_deployments":deployments,"agreement_rate":agreement}
def _report(events:list[dict[str,Any]])->None:
    s=summary(events); lines=["# Model Audit Log","","Automatically refreshed from `data/audit_events.json`. All deployments are simulations.",""]
    lines += [f"- {k.replace('_',' ').title()}: {v}" for k,v in s.items()]
    REPORT.write_text("\n".join(lines)+"\n")
def record(case_id:str, diagnosis:dict[str,Any], checker_result:list[dict[str,Any]], decision:str, override:bool=False, deployment_status:str="not_deployed")->dict[str,Any]:
    event={"case_id":case_id,"timestamp":datetime.now(timezone.utc).isoformat(),"predicted_root_cause":diagnosis.get("root_cause",""),"confidence":diagnosis.get("confidence",0),"deterministic_checker_result":checker_result,"human_decision":decision,"override":override,"deployment_status":deployment_status}
    events=_load(); events.append(event); EVENTS.write_text(json.dumps(events,indent=2)); _report(events); return event
''',
"src/engine.py": r'''"""Main diagnosis orchestrator. It only produces recommendations."""
from __future__ import annotations
from typing import Any
from .checker import check
from .llm import analyze
from .parser import validate_diagnosis
from .remediation import commands_for
def diagnose(case:dict[str,Any], config:dict[str,Any])->dict[str,Any]:
    output=str(case.get("show_outputs", "")); checker_results=check(output); hit=next((x for x in checker_results if x["detected"]),None)
    if hit:
        diagnosis={"case_id":str(case.get("case_id","UNKNOWN")),"root_cause":hit["message"],"osi_layer":"Layer 1" if hit["rule"] in {"administratively_down","line_protocol_down"} else "Layer 2","confidence":hit["confidence"],"evidence":[hit["evidence"]],"next_command":"show running-config interface <interface>","fix_steps":["Review the evidence.","Apply the recommendation only after explicit approval."],"severity":str(case.get("severity","medium")),"requires_human_approval":True}
        source="deterministic"; commands=commands_for(hit["rule"],hit["evidence"])
    else:
        try: diagnosis=validate_diagnosis(analyze(case,output,config))
        except ValueError as exc:
            diagnosis={"case_id":str(case.get("case_id","UNKNOWN")),"root_cause":f"Invalid analysis: {exc}","osi_layer":"Unknown","confidence":0.0,"evidence":[],"next_command":"show running-config","fix_steps":["Escalate for human review."],"severity":str(case.get("severity","medium")),"requires_human_approval":True}
        source="mock_llm"; commands=commands_for("unknown")
    diagnosis["requires_human_approval"]=True
    return {"diagnosis":diagnosis,"checker_results":checker_results,"recommended_commands":commands,"source":source,"simulation_only":True}
''',
"app.py": r'''"""NetSage AI Streamlit UI. It never connects to equipment."""
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
''',
"prompts/diagnose_prompt.md": '''# NetSage Diagnostic Prompt

You are an educational Cisco Packet Tracer diagnostic assistant. Use only supplied evidence. Identify an OSI layer, explain the root cause, give a calibrated 0–1 confidence score, a next *diagnostic* command, and safe remediation recommendations. Never invent outputs, execute commands, connect to hardware, claim a fix was applied, or bypass approval. Output only this strict JSON shape and always set approval to true:

```json
{"case_id":"","root_cause":"","osi_layer":"","confidence":0.0,"evidence":[],"next_command":"","fix_steps":[],"severity":"","requires_human_approval":true}
```
''',
"docs/model_audit_log.md": '''# Model Audit Log

Automatically refreshed from `data/audit_events.json`. All deployments are simulations.

- Total Diagnoses: 0
- Approved Cases: 0
- Rejected Cases: 0
- Edited Cases: 0
- Human Overrides: 0
- False Positives: 0
- Simulated Deployments: 0
- Agreement Rate: 0.0
''',
"docs/architecture.md": '''# Architecture

`cases.csv` → Streamlit → deterministic checker → mock LLM fallback → JSON validator → recommendation generator → explicit human decision → local JSON audit log. No component opens a network connection to a router or switch.\n''',
"docs/flowchart.md": '''# Diagnostic Flow

```mermaid
flowchart LR
 A[Select case] --> B[Deterministic checker]
 B -->|match| C[Evidence-based diagnosis]
 B -->|no match| D[Mock/optional LLM analysis]
 C --> E[Recommendation only]
 D --> E
 E --> F{Human decision}
 F -->|Approve| G[SIMULATED DEPLOYMENT + audit]
 F -->|Edit or Reject| H[Audit only]
```\n''',
"README.md": '''# NetSage AI: Automated Network Diagnostic Platform

NetSage AI is a safe educational Cisco Packet Tracer troubleshooting dashboard. It diagnoses supplied text outputs and produces **recommendations only**. It never connects to equipment or executes IOS commands. Every simulated deployment requires a human click.

## Install and run

```bash
pip install -r requirements.txt
streamlit run app.py
# or: python app.py (when Streamlit is installed, use its launcher above)
```

The dataset contains 30 scenarios in `data/cases.csv`; `NET-001` is the primary demo. The engine first uses deterministic regex rules, then a safe mock LLM fallback when no rule matches. A real API is intentionally not invoked by default; missing keys always fall back safely. Decisions update `data/audit_events.json` and dynamically refresh `docs/model_audit_log.md`.

## Workflow

Select NET-001, run diagnosis, review the evidence and recommended `no shutdown`, then choose Approve, Edit, or Reject. Approve displays **SIMULATED DEPLOYMENT** only; it does not apply a configuration.

See `docs/architecture.md` and `docs/flowchart.md` for design details.\n''',
"tests/test_checker.py": r'''from src.checker import check
def test_admin_down():
 r=check("GigabitEthernet0/0.30 is administratively down, line protocol is down")
 assert r[0]["rule"]=="administratively_down" and r[0]["detected"]
def test_vlan_mismatch(): assert any(x["rule"]=="vlan_mismatch" for x in check("%CDP-4-NATIVE_VLAN_MISMATCH: native vlan mismatch"))
''',
"tests/test_parser.py": r'''import pytest
from src.parser import validate_diagnosis
def payload(): return {"case_id":"X","root_cause":"x","osi_layer":"2","confidence":.5,"evidence":[],"next_command":"show x","fix_steps":[],"severity":"low","requires_human_approval":False}
def test_validation_enforces_approval(): assert validate_diagnosis(payload())["requires_human_approval"] is True
def test_bad_json():
 with pytest.raises(ValueError): validate_diagnosis("{")
''',
"tests/test_engine.py": r'''from src.engine import diagnose
def test_diagnosis_generation_and_approval():
 c={"case_id":"NET-001","severity":"high","show_outputs":"GigabitEthernet0/0.30 is administratively down, line protocol is down"}
 r=diagnose(c,{"mock_mode":True})
 assert r["source"]=="deterministic" and r["diagnosis"]["requires_human_approval"]
 assert "no shutdown" in r["recommended_commands"]
''',
"data/cases.csv": '''case_id,symptom,topology_note,concept_tag,severity,show_outputs,expected_fault
NET-001,PC1 cannot reach Server1 in VLAN 30,Router R1 to switch SW1 VLAN 30,Router-on-a-stick,high,"GigabitEthernet0/0.30 is up, line protocol is up\nGigabitEthernet0/0.30 is administratively down, line protocol is down",GigabitEthernet0/0.30 is administratively down
NET-002,PC cannot ping gateway,PC1 to SW1 access port,Interface status,high,"FastEthernet0/1 is administratively down, line protocol is down",Access interface shutdown
NET-003,Inter-switch hosts isolated,SW1 trunk to SW2,VLAN mismatch,high,"%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered",Native VLAN mismatch
NET-004,VLAN 40 clients disconnected,SW1 access VLAN 40,Missing VLAN,high,"% VLAN 40 does not exist",VLAN missing
NET-005,Trunk carries no user VLANs,SW1 to SW2 trunk,Trunking,high,"Operational mode is not trunk",Trunk mode missing
NET-006,Subinterface cannot route,R1 G0/0.20,Encapsulation,high,"encapsulation dot1Q mismatch",Incorrect dot1Q encapsulation
NET-007,Two PCs lose connectivity,LAN addressing,IP addressing,medium,"%IP-4-DUPADDR: Duplicate address",Duplicate IP address
NET-008,Host cannot reach remote subnet,PC to R1,Subnetting,medium,"Invalid mask /27 for address",Incorrect subnet mask
NET-009,Web server unreachable,PC gateway,Default gateway,high,"Default gateway 192.168.2.1 is in wrong subnet",Incorrect default gateway
NET-010,Branch network unreachable,R1 to R2,Routing,high,"Network 10.20.0.0 not in routing table",Missing route
NET-011,HTTP blocked between VLANs,R1 ACL,ACL,high,"access-list 101 deny tcp 10.1.10.0 0.0.0.255 host 10.1.20.10 eq 80",ACL deny
NET-012,Clients get APIPA addresses,SW1 DHCP relay,DHCP,high,"DHCP failed: no DHCP offers received",DHCP scope or relay issue
NET-013,Names do not resolve,PC DNS server,DNS,medium,"DNS name lookup failed: unknown host",DNS resolution failure
NET-014,Serial link unusable,R1 to R2 serial,Line protocol,high,"Serial0/0/0 is up, line protocol is down",Clocking or encapsulation issue
NET-015,Access port disabled,PC to SW1,Port security,medium,"FastEthernet0/12 is administratively down, line protocol is down",Port shutdown
NET-016,Voice VLAN phones fail,SW1 phone port,Voice VLAN,medium,"VLAN 150 not found",Voice VLAN missing
NET-017,Management SVI unreachable,SW1 VLAN 99,SVI,medium,"Vlan99 is administratively down, line protocol is down",SVI shutdown
NET-018,Native VLAN alerts,SW1 SW2,Trunking,medium,"native vlan mismatch",Native VLAN inconsistent
NET-019,Guest VLAN missing,SW1,VLAN,medium,"% VLAN 70 does not exist",Guest VLAN absent
NET-020,Internet route missing,R1 edge,Routing,high,"Default route not in routing table",Default route missing
NET-021,SSH denied,R1 ACL,ACL,high,"ACL deny tcp host 10.0.0.5 host 10.0.1.1 eq 22",ACL blocks SSH
NET-022,Subnet overlap error,R1 interfaces,IP addressing,high,"% 192.168.1.0 overlaps with GigabitEthernet0/1",Overlapping subnets
NET-023,Lab switch trunk inactive,SW1 uplink,Trunking,high,"trunking is not operational",Trunk inactive
NET-024,Subinterface sees no traffic,R1 G0/1.50,Encapsulation,high,"encapsulation is not configured",Missing encapsulation
NET-025,Campus link disabled,SW1 to core,Interface status,high,"GigabitEthernet1/0/1 is administratively down, line protocol is down",Uplink shutdown
NET-026,DHCP address unavailable,Server DHCP,DHCP,medium,"DHCP failed no address available",Exhausted DHCP pool
NET-027,DNS server unreachable,PC DNS,DNS,medium,"DNS unreachable",DNS route or address issue
NET-028,Remote VLAN blocked,R1 ACL,ACL,high,"denied by access-list 110",ACL deny
NET-029,Wrong access VLAN,PC to SW1,VLAN mismatch,medium,"inconsistent VLAN configured on interface",Access VLAN mismatch
NET-030,Unknown intermittent loss,Multi-device lab,General,low,"Interface counters increment but no known fault signature",Requires further diagnosis
'''
}

def main() -> None:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("NetSage-AI")
    destination = destination.expanduser().resolve()
    for relative, content in FILES.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dedent(content).lstrip(), encoding="utf-8")
    print(f"Created {len(FILES)} files in {destination}")
    print("Safe by design: all deployments are simulations and require approval.")

if __name__ == "__main__": main()
