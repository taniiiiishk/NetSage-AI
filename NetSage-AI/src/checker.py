"""Deterministic, evidence-only checks for simulated Cisco outputs."""
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
