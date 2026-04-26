from sqlalchemy.orm import Session
import pandas as pd
from app.models import District, WeeklyDiseaseData, WeeklyEnvironmentData, WeeklyClimateData, Week

def get_features_for_prediction(db: Session, district_name: str, year: int, week_number: int) -> dict:
    #validate district
    district = db.query(District).filter(District.district_name == district_name).first()
    if not district:
        raise ValueError(f"District '{district_name}' not found")

    district_id = district.district_id

    #validate target week exists
    target_week = db.query(Week).filter(
        Week.year == year,
        Week.week_number == week_number
    ).first()
    if not target_week:
        raise ValueError(f"Week {week_number} of year {year} not found")

    #upto last 5 weeks
    weeks = (
        db.query(Week)
        .filter(
            (Week.year < year) | ((Week.year == year) & (Week.week_number <= week_number))
        )
        .order_by(Week.year.desc(), Week.week_number.desc())
        .limit(5)
        .all()
    )
    if not weeks:
        raise ValueError("No historical week data found")

    week_ids = [w.week_id for w in reversed(weeks)]  # oldest → newest

    #disease risk(exclude other risks)
    risks_query = (
        db.query(
            WeeklyDiseaseData.week_id,
            WeeklyDiseaseData.disease_id,
            WeeklyDiseaseData.risk_level
        )
        .filter(
            WeeklyDiseaseData.district_id == district_id,
            WeeklyDiseaseData.week_id.in_(week_ids)
        )
        .all()
    )

    risks_df = pd.DataFrame(risks_query, columns=["week_id", "disease_id", "risk_level"])
    disease_map = {1: "malaria_risk", 2: "ad_risk", 3: "typhoid_risk"}

    risks_wide = pd.DataFrame(index=week_ids)
    for disease_id, col_name in disease_map.items():
        subset = risks_df[risks_df["disease_id"] == disease_id].set_index("week_id")["risk_level"]
        risks_wide[col_name] = subset.reindex(week_ids).fillna(0.0)

    #climate
    climate_query = (
        db.query(
            WeeklyClimateData.week_id,
            WeeklyClimateData.avg_temperature,
            WeeklyClimateData.avg_rainfall,
            WeeklyClimateData.avg_humidity,
        )
        .filter(
            WeeklyClimateData.district_id == district_id,
            WeeklyClimateData.week_id.in_(week_ids)
        )
        .all()
    )
    climate_df = (
        pd.DataFrame(climate_query, columns=["week_id", "avg_temperature", "avg_rainfall", "avg_humidity"])
        .set_index("week_id")
        .reindex(week_ids)
        .fillna(0.0)
    )

    #environment
    env_query = (
        db.query(
            WeeklyEnvironmentData.week_id,
            WeeklyEnvironmentData.flood_inundation,
            WeeklyEnvironmentData.stagnant_water_duration,
            WeeklyEnvironmentData.mean_ndvi,
        )
        .filter(
            WeeklyEnvironmentData.district_id == district_id,
            WeeklyEnvironmentData.week_id.in_(week_ids)
        )
        .all()
    )
    env_df = (
        pd.DataFrame(env_query, columns=["week_id", "flood_inundation", "stagnant_water_duration", "mean_ndvi"])
        .set_index("week_id")
        .reindex(week_ids)
        .rename(columns={"stagnant_water_duration": "stagnant_water"})
        .fillna(0.0)
    )

    #lag/roll
    def extract_features(series: pd.Series) -> tuple:
        if len(series) == 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        current = series.iloc[-1]
        lag1 = series.shift(1).iloc[-1] if len(series) > 1 else 0.0
        lag2 = series.shift(2).iloc[-1] if len(series) > 2 else 0.0
        roll3 = series.tail(3).mean() if len(series) >= 3 else series.mean()
        roll5 = series.tail(5).mean() if len(series) >= 5 else series.mean()
        return current, lag1, lag2, roll3, roll5

    #static features
    shared = {
        "district": str(district_id),
        "population": float(district.population or 0),
        "elevation_m": float(district.elevation_m or 0),
        "river_status": float(district.river_status or 0),
        "area_sq_km": float(district.area_sq_km or 0),
        "sanitation_index": float(district.sanitation_index or 0),
    }

    #env/climate features shared acroos diseases
    for col in ["avg_temperature", "avg_rainfall", "avg_humidity"]:
        cur, l1, l2, r3, r5 = extract_features(climate_df[col])
        shared[col] = cur
        shared[f"{col}_lag1"] = l1
        shared[f"{col}_lag2"] = l2
        shared[f"{col}_roll3"] = r3
        shared[f"{col}_roll5"] = r5

    for col in ["flood_inundation", "stagnant_water", "mean_ndvi"]:
        cur, l1, l2, r3, r5 = extract_features(env_df[col])
        shared[col] = cur
        shared[f"{col}_lag1"] = l1
        shared[f"{col}_lag2"] = l2
        shared[f"{col}_roll3"] = r3
        shared[f"{col}_roll5"] = r5

    #per-disease feature set
    malaria_features = shared.copy()
    ad_features     = shared.copy()
    typhoid_features = shared.copy()

    #disease specific feature set
    for disease, feat_dict in [
        ("malaria_risk", malaria_features),
        ("ad_risk",     ad_features),
        ("typhoid_risk", typhoid_features)
    ]:
        series = risks_wide[disease]
        cur, l1, l2, r3, r5 = extract_features(series)
        feat_dict[disease]          = cur
        feat_dict[f"{disease}_lag1"] = l1
        feat_dict[f"{disease}_lag2"] = l2
        feat_dict[f"{disease}_roll3"] = r3
        feat_dict[f"{disease}_roll5"] = r5

    return {
        "malaria": malaria_features,
        "ad": ad_features,
        "typhoid": typhoid_features
    }

def get_all_district_latest_risks(db: Session):
    """
    Returns risk scores for the MOST RECENT week available in the database.
    This is used by the Choropleth Map.
    """
    from app.models import District, WeeklyDiseaseData, Week
    from sqlalchemy import desc, func

    # Get the absolute latest week in the database
    latest_week = db.query(Week).order_by(desc(Week.year), desc(Week.week_number)).first()
    if not latest_week:
        return []

    # Fetch risk data for that latest week
    query = db.query(
        District.district_name,
        WeeklyDiseaseData.disease_id,
        func.coalesce(WeeklyDiseaseData.risk_level, 0.0).label("risk_level")
    ).outerjoin(
        WeeklyDiseaseData,
        (District.district_id == WeeklyDiseaseData.district_id) &
        (WeeklyDiseaseData.week_id == latest_week.week_id-1)
    ).all()

    result = {}
    disease_map = {1: "malaria", 2: "diarrhea", 3: "typhoid"}

    for row in query:
        dist_name = (row.district_name or "Unknown").strip()

        if dist_name not in result:
            result[dist_name] = {
                "district_name": dist_name,
                "adm2_pcode": dist_name,           # fallback for choropleth
                "risk_malaria": 0.0,
                "risk_diarrhea": 0.0,
                "risk_typhoid": 0.0,
                "week_info": f"Week {latest_week.week_number-1} ({latest_week.year})"   # optional but useful
            }

        disease_key = disease_map.get(row.disease_id)
        if disease_key:
            result[dist_name][f"risk_{disease_key}"] = float(row.risk_level)

    return list(result.values())

def get_district_risk_history(db: Session, identifier: str, weeks_back: int = 12):
    """
    Returns historical risk data for a district.
    Accepts either district_name or adm2_pcode (tries name first).
    """
    from app.models import District, WeeklyDiseaseData, Week
    from sqlalchemy import desc

    # Try to find district by name (most reliable)
    district = db.query(District).filter(District.district_name == identifier).first()

    # If not found, try as pcode (fallback - using district_name as pcode for now)
    if not district:
        district = db.query(District).filter(District.district_name == identifier).first()

    if not district:
        raise ValueError(f"District with identifier '{identifier}' not found")

    # Get recent weeks
    recent_weeks = (
        db.query(Week)
        .order_by(desc(Week.year), desc(Week.week_number))
        .limit(weeks_back)
        .all()
    )

    if not recent_weeks:
        return []

    week_ids = [w.week_id for w in recent_weeks]

    # Fetch risk data
    risks_query = (
        db.query(
            Week.year,
            Week.week_number,
            WeeklyDiseaseData.disease_id,
            WeeklyDiseaseData.risk_level
        )
        .join(WeeklyDiseaseData, WeeklyDiseaseData.week_id == Week.week_id)
        .filter(
            WeeklyDiseaseData.district_id == district.district_id,
            WeeklyDiseaseData.week_id.in_(week_ids)
        )
        .order_by(Week.year, Week.week_number)
        .all()
    )

    result = []
    disease_map = {1: "malaria", 2: "diarrhea", 3: "typhoid"}

    from collections import defaultdict
    week_data = defaultdict(lambda: {
        "week": "",
        "risk_malaria": 0.0,
        "risk_diarrhea": 0.0,
        "risk_typhoid": 0.0
    })

    for row in risks_query:
        week_label = f"Week {row.week_number} ({row.year})"
        disease_key = disease_map.get(row.disease_id)
        if disease_key:
            week_data[week_label][f"risk_{disease_key}"] = float(row.risk_level or 0.0)

    for week_label in sorted(week_data.keys()):
        week_data[week_label]["week"] = week_label
        result.append(week_data[week_label])

    return result