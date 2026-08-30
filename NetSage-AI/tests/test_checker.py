from src.checker import check
def test_admin_down():
 r=check("GigabitEthernet0/0.30 is administratively down, line protocol is down")
 assert r[0]["rule"]=="administratively_down" and r[0]["detected"]
def test_vlan_mismatch(): assert any(x["rule"]=="vlan_mismatch" for x in check("%CDP-4-NATIVE_VLAN_MISMATCH: native vlan mismatch"))
