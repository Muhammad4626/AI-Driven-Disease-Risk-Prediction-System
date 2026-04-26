import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import get_features_for_prediction, get_all_district_latest_risks, get_district_risk_history
from app.predict import run_prediction

app = FastAPI(title="AI Disease Risk Prediction API")

# CORS for production
def get_cors_origins():
    raw = os.getenv("CORS_ORIGINS", "https://core.bugdoubt.com,http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter
api_router = APIRouter(prefix="/api")


@api_router.get("/predict")
def predict(
    district_name: str = Query(..., description="Exact district name"),
    year: int = Query(..., ge=2000, le=2100),
    week_number: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db)
):
    try:
        features_dict = get_features_for_prediction(db, district_name, year, week_number)
        predictions = run_prediction(features_dict)

        return {
            "district_name": district_name,
            "year": year,
            "week_number": week_number,
            "predictions": predictions
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@api_router.get("/districts/risks")
def get_districts_risks(db: Session = Depends(get_db)):
    try:
        risks = get_all_district_latest_risks(db)
        return {"data": risks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/districts/{identifier}/history")
def get_district_history(
    identifier: str,
    weeks_back: int = Query(12, ge=4, le=52),
    db: Session = Depends(get_db)
):
    try:
        history = get_district_risk_history(db, identifier, weeks_back)
        return {"data": history}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "healthy"}