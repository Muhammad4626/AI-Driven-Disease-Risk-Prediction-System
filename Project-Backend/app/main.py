import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from dotenv import load_dotenv

load_dotenv()  # allow local `.env` usage; no-op in production if not present

from app.auth import authenticate_user, create_access_token, get_current_user, register_user
from app.database import get_db
from app.crud import (
    get_features_for_prediction,
    get_all_district_latest_risks,
    get_district_risk_history,
    get_user_by_email,
    get_cumulative_cases_by_disease,
)
from app.models import User
from app.predict import run_prediction
from app.schemas import LoginRequest, LoginResponse, RegisterRequest, UserOut

app = FastAPI(title="AI Disease Risk Prediction API")

def get_cors_origins():
    """
    Comma-separated list in env: CORS_ORIGINS=https://core.example.com,http://localhost:3000
    If unset, defaults to common local dev origins.
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]

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

@api_router.get("/summary/cases")
def get_cumulative_cases(
    disease: str = Query(..., description="Disease key: malaria | typhoid | ad | diarrhea"),
    db: Session = Depends(get_db),
):
    """
    Returns cumulative (all-time) total cases for the selected disease across Pakistan.
    """
    try:
        total_cases = get_cumulative_cases_by_disease(db, disease)
        return {"disease": disease, "total_cases": total_cases}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=LoginResponse)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_request.email, login_request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(subject=user.user_email, user_id=user.user_id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@api_router.post("/auth/register", response_model=LoginResponse)
def register(register_request: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, register_request.email):
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = register_user(db, register_request.name, register_request.email, register_request.password)
    if user is None:
        raise HTTPException(status_code=500, detail="Unable to create user")

    access_token = create_access_token(subject=user.user_email, user_id=user.user_id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@api_router.get("/auth/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "healthy"}