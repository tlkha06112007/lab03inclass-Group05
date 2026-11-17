## Run the assistant (backend + UI)

Copy `.env.example` to `.env` and set `SESSION_SALT` and `API_ADMIN_KEY`.
Open two terminals in `assistant_core_lab` with the virtual environment active:

```
# terminal 1 - backend (API, port 8000)
uvicorn assistant_api.main:create_app --factory --reload

# terminal 2 - UI (Streamlit, port 8501)
streamlit run ui/app.py
```

Then open http://localhost:8501. If the API runs on another address, set `ASSISTANT_API_URL`.
