"""Recommendation-only IOS snippets. These strings are never executed."""
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
