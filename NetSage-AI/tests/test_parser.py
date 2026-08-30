import pytest
from src.parser import validate_diagnosis
def payload(): return {"case_id":"X","root_cause":"x","osi_layer":"2","confidence":.5,"evidence":[],"next_command":"show x","fix_steps":[],"severity":"low","requires_human_approval":False}
def test_validation_enforces_approval(): assert validate_diagnosis(payload())["requires_human_approval"] is True
def test_bad_json():
 with pytest.raises(ValueError): validate_diagnosis("{")
