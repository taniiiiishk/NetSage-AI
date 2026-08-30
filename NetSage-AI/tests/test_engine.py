from src.engine import diagnose
def test_diagnosis_generation_and_approval():
 c={"case_id":"NET-001","severity":"high","show_outputs":"GigabitEthernet0/0.30 is administratively down, line protocol is down"}
 r=diagnose(c,{"mock_mode":True})
 assert r["source"]=="deterministic" and r["diagnosis"]["requires_human_approval"]
 assert "no shutdown" in r["recommended_commands"]
