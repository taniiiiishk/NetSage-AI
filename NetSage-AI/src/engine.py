"""Main diagnosis orchestrator. It only produces recommendations."""
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
