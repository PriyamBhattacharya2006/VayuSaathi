# VayuSaathi Full-Stack (FastAPI + Gemini + SQLite)

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Optional: add your GEMINI_API_KEY
uvicorn app:app --reload --port 8000
```
Open `http://127.0.0.1:8000` in your browser.

## Deploy to Render / Railway
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Environment Variable (optional):** `GEMINI_API_KEY`
 https://priyambhattacharya2006.github.io/VayuSaathi/
