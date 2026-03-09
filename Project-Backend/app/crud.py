from sqlalchemy.orm import Session
import pandas as pd
from app.models import District, WeeklyDiseaseData, WeeklyEnvironmentData, WeeklyClimateData, Week

def get_features_for_prediction(db: Session, district_name: str, year: int, week_number: int) -> dict:
    """
    Fetch last up to 5 weeks of data and compute features.
    Returns dict with three keys: 'malaria', 'ad', 'typhoid' — each with its own feature set.
    """
    # ── 1. Validate district ────────────────────────────────────────────────
    district = db.query(District).filter(District.district_name == district_name).first()
    if not district:
        raise ValueError(f"District '{district_name}' not found")

    district_id = district.district_id

    # ── 2. Validate target week exists ──────────────────────────────────────
    target_week = db.query(Week).filter(
        Week.year == year,
        Week.week_number == week_number
    ).first()
    if not target_week:
        raise ValueError(f"Week {week_number} of year {year} not found")

    # ── 3. Get up to last 5 weeks (including target) ────────────────────────
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

    # ── 4. Disease risks (wide format: one column per disease) ──────────────
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

    # ── 5. Climate ──────────────────────────────────────────────────────────
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

    # ── 6. Environment ──────────────────────────────────────────────────────
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

    # ── 7. Helper to compute current + lag1/lag2/roll3/roll5 ────────────────
    def extract_features(series: pd.Series) -> tuple:
        if len(series) == 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        current = series.iloc[-1]
        lag1 = series.shift(1).iloc[-1] if len(series) > 1 else 0.0
        lag2 = series.shift(2).iloc[-1] if len(series) > 2 else 0.0
        roll3 = series.tail(3).mean() if len(series) >= 3 else series.mean()
        roll5 = series.tail(5).mean() if len(series) >= 5 else series.mean()
        return current, lag1, lag2, roll3, roll5

    # ── 8. Shared base features ─────────────────────────────────────────────
    shared = {
        "district": str(district_id),
        "population": float(district.population or 0),
        "elevation_m": float(district.elevation_m or 0),
        "river_status": float(district.river_status or 0),
        "area_sq_km": float(district.area_sq_km or 0),
        "sanitation_index": float(district.sanitation_index or 0),
    }

    # Add env/climate to shared
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

    # ── 9. Create per-disease feature sets ──────────────────────────────────
    malaria_features = shared.copy()
    ad_features     = shared.copy()
    typhoid_features = shared.copy()

    # Add disease-specific features
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