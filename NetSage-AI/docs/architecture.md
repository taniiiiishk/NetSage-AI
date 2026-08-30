# Architecture

`cases.csv` → Streamlit → deterministic checker → mock LLM fallback → JSON validator → recommendation generator → explicit human decision → local JSON audit log. No component opens a network connection to a router or switch.
