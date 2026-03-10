from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import get_features_for_prediction
from app.predict import run_prediction

app = FastAPI(title="AI Disease Risk Prediction API")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/predict")
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