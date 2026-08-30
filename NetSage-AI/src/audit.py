"""Local audit trail for decisions and explicitly simulated deployments."""
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
