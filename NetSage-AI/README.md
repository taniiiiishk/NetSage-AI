# NetSage AI: Automated Network Diagnostic Platform

NetSage AI is a safe educational Cisco Packet Tracer troubleshooting dashboard. It diagnoses supplied text outputs and produces **recommendations only**. It never connects to equipment or executes IOS commands. Every simulated deployment requires a human click.

## Install and run

```bash
pip install -r requirements.txt
streamlit run app.py
# or: python app.py (when Streamlit is installed, use its launcher above)
```

The dataset contains 30 scenarios in `data/cases.csv`; `NET-001` is the primary demo. The engine first uses deterministic regex rules, then a safe mock LLM fallback when no rule matches. A real API is intentionally not invoked by default; missing keys always fall back safely. Decisions update `data/audit_events.json` and dynamically refresh `docs/model_audit_log.md`.

## Workflow

Select NET-001, run diagnosis, review the evidence and recommended `no shutdown`, then choose Approve, Edit, or Reject. Approve displays **SIMULATED DEPLOYMENT** only; it does not apply a configuration.

See `docs/architecture.md` and `docs/flowchart.md` for design details.
