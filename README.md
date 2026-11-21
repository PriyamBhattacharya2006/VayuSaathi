# VayuSaathi v2.0 — GenAI Winter Smog & Urban Air Quality Assistant

> **Evidence-based winter smog navigation, 24-hour diurnal inversion forecasts, indoor air quality simulator, DIY Corsi-Rosenthal purifier blueprints, and community action.**

Live Web Application: [https://priyambhattacharya2006.github.io/VayuSaathi/](https://priyambhattacharya2006.github.io/VayuSaathi/)

---

## ✨ Features

- 🌫️ **Dynamic Atmospheric AQI Engine**: Real-time ambient UI glow and grounded winter monitoring data across Kolkata (WBPCB), Delhi-NCR (CPCB), Mumbai, Patna, and Lucknow.
- 🕒 **24-Hour Diurnal Inversion & Safe Window Forecast**: Visualizes thermal boundary layer trapping and identifies peak hazard hours (6–10 AM) vs safe solar dispersion windows (1–4 PM).
- 🏠 **Interactive IAQ Room Simulator**: Calculates Air Changes per Hour (ACH), time to clear 80% room smoke, and models DIY Corsi-Rosenthal boxes vs commercial HEPA filters and indoor hazards (mosquito coils, incense, cooking).
- 🫁 **Lung Inhalation Dose Calculator**: Quantifies actual micrograms ($\mu\text{g}$) of $\text{PM}_{2.5}$ deposited deep into alveolar capillaries across commute modes and compares N95 vs surgical vs cloth mask filtration.
- 💬 **GenAI Assistant with Voice & Audio**: Conversational assistant powered by Gemini 2.5 Flash with Web Speech voice input and Text-to-Speech (TTS) read-aloud capabilities.
- 📢 **Community Action & WhatsApp Generator**: Generates formatted anti-burning notices and carpool advisories with 1-click sharing to WhatsApp and community hotspot logging.
- 🩺 **Vulnerability Protocols & Myth Busters**: Clinically grounded winter smog guidance for children, asthma patients, and seniors, debunking common myths (jaggery, snake plants, cloth masks).
- 🖨️ **Printable Smog Defense Card**: Export clean, fridge-friendly daily action cards.

---

## 🚀 Run Locally

```bash
# 1. Clone & create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure Gemini API Key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key

# 4. Start FastAPI server
uvicorn app:app --reload --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. (The web app is also fully functional as a static PWA directly via `index.html`).

---

## ☁️ Deploy to Render / Railway
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Environment Variable (optional):** `GEMINI_API_KEY`
