"""Optional LLM adapter; mock mode is the safe default and never executes commands."""
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
