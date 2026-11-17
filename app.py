import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "vayusaathi.db"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="VayuSaathi API",
    description="GenAI-powered winter smog & urban air quality assistant backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Grounded WBPCB Kolkata Station Readings (Nov 17, 2026)
STATIONS = {
    "kolkata": {"name": "Kolkata Overall", "aqi": 270},
    "chakraberia": {"name": "Chakraberia", "aqi": 282},
    "bhowanipore": {"name": "Bhowanipore", "aqi": 276},
    "ballygunge": {"name": "Ballygunge", "aqi": 272},
    "bidhannagar": {"name": "Bidhannagar / Salt Lake", "aqi": 264},
    "jadavpur": {"name": "Jadavpur University", "aqi": 218},
    "fort_william": {"name": "Fort William", "aqi": 177},
    "rabindra_sarobar": {"name": "Rabindra Sarobar", "aqi": 125},
}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS community_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station TEXT NOT NULL,
                aqi INTEGER NOT NULL,
                campaign_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()


class ImpactRequest(BaseModel):
    aqi: int = Field(270, ge=0, le=500)
    commute_km: float = Field(15.0, ge=1.0, le=150.0)
    cooking: str = "lpg"
    active_iaq_hacks: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    station_id: str = "kolkata"
    aqi: int = Field(270, ge=0, le=500)
    household: str = "family_kids_seniors"
    commute: str = "car"
    cooking: str = "lpg"
    commute_km: float = Field(15.0, ge=1.0, le=150.0)
    active_iaq_hacks: List[str] = Field(default_factory=list)


class AlertCreate(BaseModel):
    station: str
    aqi: int = Field(..., ge=0, le=500)
    campaign_type: str
    message: str = Field(..., min_length=5, max_length=2000)


def estimate_pm25_from_aqi(aqi: int) -> int:
    if aqi <= 50:
        return round((aqi / 50) * 30)
    if aqi <= 100:
        return round(30 + ((aqi - 50) / 50) * 30)
    if aqi <= 200:
        return round(60 + ((aqi - 100) / 100) * 30)
    if aqi <= 300:
        return round(90 + ((aqi - 200) / 100) * 30)
    if aqi <= 400:
        return round(120 + ((aqi - 300) / 100) * 130)
    return round(250 + ((aqi - 400) / 100) * 100)


def compute_impact_metrics(req: ImpactRequest) -> dict:
    outdoor_pm = estimate_pm25_from_aqi(req.aqi)
    hacks = set(req.active_iaq_hacks)
    indoor_base = outdoor_pm * (0.42 if "seal_inversion" in hacks else 0.65)

    cooking_spike = 0.0
    if req.cooking == "lpg":
        cooking_spike = 11.4
    elif req.cooking == "hybrid":
        cooking_spike = 5.7
    if "kitchen_exhaust" in hacks:
        cooking_spike *= 0.35

    indoor_total = indoor_base + cooking_spike
    if "cr_box" in hacks:
        indoor_total *= 1 - 0.72
    if "wet_mop" in hacks:
        indoor_total *= 1 - 0.10

    indoor_pm = max(4, round(indoor_total))
    exposure_cut = max(0, round(((outdoor_pm - indoor_pm) / max(1, outdoor_pm)) * 100))

    car_daily_co2 = (req.commute_km * 111) / 1000.0
    metro_daily_co2 = car_daily_co2 / 6.5
    co2_avoidable = max(0.0, car_daily_co2 - metro_daily_co2)

    return {
        "outdoor_pm25": outdoor_pm,
        "indoor_pm25": indoor_pm,
        "exposure_cut_pct": exposure_cut,
        "car_daily_co2_kg": round(car_daily_co2, 2),
        "metro_daily_co2_kg": round(metro_daily_co2, 2),
        "co2_avoidable_kg": round(co2_avoidable, 2),
    }


def deterministic_assistant(req: ChatRequest, metrics: dict) -> dict:
    station_name = STATIONS.get(req.station_id, {}).get("name", "your area")
    q = req.prompt.lower()
    if "corsi" in q or "diy" in q or "purifier" in q:
        return {
            "title": "DIY Corsi-Rosenthal Box Plan",
            "answer": (
                f"At {station_name} (AQI {req.aqi}), outdoor PM2.5 is ~{metrics['outdoor_pm25']} ug/m3. "
                "A 5-filter MERV-13 Corsi-Rosenthal Box delivers 600-850 ft3/min CADR at ~1/10th the cost of commercial HEPA."
            ),
            "impact": (
                f"Verified Impact: Cuts PM2.5 mass by >70% (estimated indoor level ~{max(6, round(metrics['indoor_pm25'] * 0.35))} ug/m3) "
                "and reduces fine particles by 56-91%."
            ),
            "source": "fallback",
        }
    if "lpg" in q or "induction" in q or "cook" in q:
        return {
            "title": "Kitchen Fuel & Indoor Air Impact",
            "answer": (
                f"Shifting high-boil meals from LPG to induction reduces indoor combustion pollution for your {req.household.replace('_', ' ')}."
            ),
            "impact": (
                "Verified Impact: LPG increases 48-hr personal NO2 by 50% (+9.9 ppb) and personal PM2.5 by 44% (+11.4 ug/m3). "
                "Induction cuts 100% of direct CO2 and 94.4% of CO."
            ),
            "source": "fallback",
        }
    if "commute" in q or "metro" in q or "car" in q:
        return {
            "title": f"Low-Emission Commute for {station_name}",
            "answer": (
                f"For your {req.commute_km:.0f} km daily round trip, shifting from a private car to Kolkata Metro or bus avoids peak roadside exhaust."
            ),
            "impact": (
                f"Verified Impact: Saves ~{metrics['co2_avoidable_kg']:.2f} kg CO2/day (~{metrics['co2_avoidable_kg'] * 22:.1f} kg/month). "
                "Kolkata car users emit 6.5x more carbon per capita than Metro riders."
            ),
            "source": "fallback",
        }
    return {
        "title": f"Today's Smog Strategy for {station_name} (AQI {req.aqi})",
        "answer": (
            f"With outdoor PM2.5 at ~{metrics['outdoor_pm25']} ug/m3, avoid morning walks before 10:30 AM, "
            "cross-ventilate briefly between 1-4 PM, and seal windows before evening NO2 peaks."
        ),
        "impact": (
            f"Your current home setup brings indoor PM2.5 to ~{metrics['indoor_pm25']} ug/m3 ({metrics['exposure_cut_pct']}% lower than outdoors)."
        ),
        "source": "fallback",
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


@app.get("/api/stations")
def get_stations():
    return {"stations": STATIONS}


@app.post("/api/impact")
def calculate_impact(req: ImpactRequest):
    return compute_impact_metrics(req)


@app.post("/api/chat")
def chat_assistant(req: ChatRequest):
    metrics = compute_impact_metrics(
        ImpactRequest(
            aqi=req.aqi,
            commute_km=req.commute_km,
            cooking=req.cooking,
            active_iaq_hacks=req.active_iaq_hacks,
        )
    )
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            station_name = STATIONS.get(req.station_id, {}).get("name", "Kolkata")
            system_context = (
                "You are VayuSaathi, a concise, evidence-based winter smog assistant for urban Indian families. "
                f"User context: Station={station_name}, AQI={req.aqi} (Est. Outdoor PM2.5={metrics['outdoor_pm25']} ug/m3), "
                f"Est. Indoor PM2.5={metrics['indoor_pm25']} ug/m3, Household={req.household}, Commute={req.commute} ({req.commute_km} km/day), "
                f"Cooking={req.cooking}, Active IAQ Hacks={req.active_iaq_hacks}. "
                "Give practical, tailored advice in 2-3 sentences and clearly explain the direct quantified impact."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_context}\n\nUser Question: {req.prompt}",
            )
            text = (response.text or "").strip()
            if text:
                return {
                    "title": f"VayuSaathi AI · {station_name} (AQI {req.aqi})",
                    "answer": text,
                    "impact": (
                        f"Profile Context: Indoor PM2.5 ~{metrics['indoor_pm25']} ug/m3 "
                        f"({metrics['exposure_cut_pct']}% below outdoors) · Commute savings {metrics['co2_avoidable_kg']} kg CO2/day"
                    ),
                    "source": "gemini",
                }
        except Exception:
            pass

    return deterministic_assistant(req, metrics)


@app.get("/api/community-alerts")
def list_alerts():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, station, aqi, campaign_type, message, created_at FROM community_alerts ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return {"alerts": [dict(r) for r in rows]}


@app.post("/api/community-alerts")
def create_alert(alert: AlertCreate):
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO community_alerts (station, aqi, campaign_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (alert.station, alert.aqi, alert.campaign_type, alert.message, now),
        )
        conn.commit()
        alert_id = cur.lastrowid
    return {"id": alert_id, "status": "saved", "created_at": now}


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    return FileResponse(str(index_path))
