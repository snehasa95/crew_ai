# CrewBank Assistant

A proof-of-concept conversational banking assistant built with Streamlit and CrewAI. The project follows MVC boundaries:

- `models/`: SQLite banking data and simulated MCP tools.
- `services/`: ChatGroq provider configuration.
- `controllers/`: CrewAI coordinator and specialist-agent workflow.
- `views/`: Streamlit chat interface.

## Run on Windows

Use Python 3.10 through 3.13. CrewAI is not currently installable in the Python 3.14 environment shipped with this workspace.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Set `GROQ_API_KEY` in `.env`. The configured free-tier model is exactly `openai/gpt-oss-120b`. The app also accepts the existing lowercase `groq_api_key` variable for compatibility.

The app creates `bank_data.db` on startup and uses the fixed demo context `USR-1001` / `ACC-1001`. There is intentionally no authentication or authorization. The crew uses `max_rpm=900`, exponential Tenacity retries for rate-limit errors, and a small request delay.
