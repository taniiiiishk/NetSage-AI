# NetSage AI: Automated Network Diagnostic Platform

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B.svg)](https://streamlit.io/)
[![Safety Standard](https://img.shields.io/badge/Execution-Simulated%20Only-22c55e.svg)](#safety--non-destructive-guarantee)
[![Governance](https://img.shields.io/badge/HITL-Mandatory%20Approval-6366f1.svg)](#human-in-the-loop-hitl-governance)

**NetSage AI** is an intelligent, educational network troubleshooting and diagnostic platform tailored for Cisco Packet Tracer scenarios and enterprise network environments. It bridges deterministic signature analysis, large language model (LLM) reasoning, and strict Human-in-the-Loop (HITL) safety controls to diagnose and remediate network incidents without any risk of destructive changes.

---

## 📌 Problem Statement

Network troubleshooting in enterprise environments and educational labs (e.g. Cisco CCNA/CCNP, Packet Tracer) often involves deciphering dense CLI `show` command outputs across multiple OSI layers. Novice engineers frequently struggle to pinpoint root causes, while automated remediation scripts can risk service outages if executed autonomously without human validation.

## 🎯 Project Objective

NetSage AI delivers:
1. **Automated Root-Cause Analysis**: Quickly isolates faults across OSI Layers 1 through 7 from raw Cisco show outputs.
2. **Deterministic & AI Dual-Core Engine**: Combines regex pattern matching for known fault signatures with an LLM reasoning engine for complex scenarios.
3. **100% Offline Capability**: Runs completely out-of-the-box with zero external API key requirements via its built-in Mock Reasoning Engine, while supporting optional live Gemini LLM APIs.
4. **Mandatory Human-in-the-Loop (HITL)**: Requires explicit operator approval, command editing, or rejection before any action.
5. **Software-Only Simulated Deployment**: Safely emulates Cisco IOS configuration pushes in software with zero connection to physical networking hardware.
6. **Continuous Model Auditability**: Tracks human agreement rates, operator overrides, and false positives in real time.

---

## 🏛️ System Architecture

```
NetSage-AI/
│
├── README.md                  # Comprehensive platform documentation
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment configuration template
├── .gitignore                 # Git ignore rules
├── app.py                     # Streamlit web dashboard & NOC UI
│
├── data/
│   ├── cases.csv              # 30 structured Cisco Packet Tracer scenarios
│   └── system_config.json     # Platform runtime parameters
│
├── src/
│   ├── __init__.py            # Package initialization
│   ├── checker.py             # Deterministic regex signature analyzer
│   ├── engine.py              # Master diagnostic & HITL orchestrator
│   ├── llm.py                 # LLM engine (Offline Mock + Live Gemini)
│   ├── parser.py              # Pydantic schema validation & JSON parser
│   ├── remediation.py         # Safe Cisco IOS remediation generator
│   └── audit.py               # Dynamic audit ledger & metrics tracker
│
├── prompts/
│   └── diagnose_prompt.md     # CCIE-level diagnostic system prompt
│
├── docs/
│   ├── model_audit_log.md     # Dynamically generated audit ledger
│   ├── architecture.md        # Technical architecture specifications
│   └── flowchart.md           # Mermaid workflow and decision diagrams
│
└── tests/
    ├── test_checker.py        # Deterministic rule unit tests
    ├── test_parser.py         # JSON schema & recovery tests
    └── test_engine.py         # Integration & HITL pipeline tests
```

---

## ⚡ Key Features

- **Dual-Core Diagnostic Pipeline**:
  - **Deterministic Rule Engine (`checker.py`)**: Instant, zero-latency detection of `administratively down`, `Native VLAN mismatch`, `missing VLAN`, `OSPF area mismatch`, `ACL deny`, `DHCP helper missing`, and `duplex mismatch`.
  - **LLM Reasoning Core (`llm.py`)**: Contextual root cause derivation, OSI layer mapping, forensic evidence extraction, and post-verification commands.
- **Human-in-the-Loop (HITL) Controls**:
  - `[✅ Approve & Deploy Fix]`: Simulates Cisco CLI push with execution logging.
  - `[✏️ Edit Commands]`: Allows engineers to customize IOS commands prior to simulated execution.
  - `[❌ Reject]`: Flags false positives and records operator feedback.
- **30 Realistic Packet Tracer Scenarios (`data/cases.csv`)**:
  - Comprehensive coverage of sub-interfaces, trunking, routing (OSPF, RIP), ACLs, EtherChannel, DHCP snooping, HSRP, IPv6, NTP, and SSH.
- **Real-Time Audit & Quality Ledger (`docs/model_audit_log.md`)**:
  - Computes Dynamic Agreement Rates, Approval %, Rejection %, and Operator Override metrics.

---

## 🔒 Safety & Non-Destructive Guarantee

> [!IMPORTANT]
> **SIMULATION ONLY**: NetSage AI contains no SSH, Telnet, or hardware driver libraries. All command deployments occur in an in-memory simulated virtual terminal.
> **HUMAN APPROVAL REQUIRED**: The system will NEVER autonomously push configuration changes.

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 2. Clone / Setup Workspace
```bash
cd /Users/tanishkyadav/.gemini/antigravity/scratch/NetSage-AI
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure Live API Key
If you wish to use live Google Gemini models, copy `.env.example` to `.env` and set your key:
```bash
cp .env.example .env
# Edit .env and set:
# GEMINI_API_KEY=your_actual_key_here
```
*Note: If no API key is provided, NetSage AI runs seamlessly in Offline Mock Engine mode.*

### 5. Launch the Dashboard
```bash
streamlit run app.py
```
Or alternatively:
```bash
python -m streamlit run app.py
```

The Streamlit NOC dashboard will open in your browser at `http://localhost:8501`.

---

## 🧪 Demonstration Scenario: NET-001 Walkthrough

### Scenario Context
- **Case ID**: `NET-001`
- **Symptom**: "PC1 cannot reach Server1 in VLAN 30"
- **Topology**: Router R1 connects to Switch SW1 via trunk link. PC1 is connected to SW1 in VLAN 30.
- **Cisco Show Output**:
  ```text
  R1# show ip interface brief
  GigabitEthernet0/0.30  192.168.30.1  YES manual administratively down down

  R1# show interfaces GigabitEthernet0/0.30
  GigabitEthernet0/0.30 is administratively down, line protocol is down
  ```

### Step-by-Step Workflow in NetSage AI
1. **Select Incident**: Choose `NET-001` from the sidebar dropdown.
2. **Click `[🚀 Run Automated Diagnosis]`**:
   - The deterministic engine detects `AdministrativelyDownRule` (Confidence: `98%`).
   - Root Cause: `GigabitEthernet0/0.30 is administratively down.`
   - OSI Layer: `Layer 1 - Physical`.
   - Proposed Fix:
     ```cisco
     configure terminal
     interface GigabitEthernet0/0.30
     no shutdown
     end
     write memory
     ```
3. **Review & Authorize**:
   - Click `[✅ Approve & Deploy Fix]`.
   - The virtual terminal executes the commands and displays:
     ```text
     NetSage-SimTerminal(config)#interface GigabitEthernet0/0.30
     NetSage-SimTerminal(config-if)#no shutdown
     [SIMULATED DEPLOYMENT SUCCESSFUL - ZERO PHYSICAL IMPACT]
     ```
   - The decision is immediately recorded in `docs/model_audit_log.md`.

---

## 🔬 Running Automated Tests

Run the complete test suite using `pytest`:

```bash
pytest -v tests/
```

Test coverage includes:
- `tests/test_checker.py`: Validates deterministic detection of administrative down, VLAN mismatches, ACL drops, and line protocol failures.
- `tests/test_parser.py`: Validates JSON schema integrity, pydantic field constraints, and heuristic recovery.
- `tests/test_engine.py`: Validates end-to-end orchestration, mock LLM fallback, and the mandatory human approval gate.
# NetSage-AI
