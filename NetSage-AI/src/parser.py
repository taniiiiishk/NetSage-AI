"""Validation for structured diagnostic responses."""
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
