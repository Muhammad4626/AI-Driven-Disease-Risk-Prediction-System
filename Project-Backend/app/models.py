from sqlalchemy import Column, Integer, Float, String, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class District(Base):
    __tablename__ = "district"
    district_id = Column(Integer, primary_key=True)
    district_name = Column(String(70))
    population = Column(Float)
    elevation_m = Column(Float)
    river_status = Column(Float)
    area_sq_km = Column(Float)
    sanitation_index = Column(Float)
    province = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)

class Disease(Base):
    __tablename__ = "disease"
    disease_id = Column(Integer, primary_key=True)
    disease_name = Column(String(100))
    category = Column(String(50))

class Week(Base):
    __tablename__ = "week"
    week_id = Column(Integer, primary_key=True)
    year = Column(Integer)
    week_number = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)

class WeeklyDiseaseData(Base):
    __tablename__ = "weekly_disease_data"
    weekly_disease_id = Column(Integer, primary_key=True)
    cases_count = Column(Integer)
    risk_level = Column(Float)          # Now matches your DB change
    district_id = Column(Integer, ForeignKey("district.district_id"))
    week_id = Column(Integer, ForeignKey("week.week_id"))
    disease_id = Column(Integer, ForeignKey("disease.disease_id"))

class WeeklyClimateData(Base):
    __tablename__ = "weekly_climate_data"
    weekly_climate_id = Column(Integer, primary_key=True)
    avg_temperature = Column(Float)
    avg_rainfall = Column(Float)
    avg_humidity = Column(Float)
    district_id = Column(Integer, ForeignKey("district.district_id"))
    week_id = Column(Integer, ForeignKey("week.week_id"))

class WeeklyEnvironmentData(Base):
    __tablename__ = "weekly_environment_data"
    weekly_env_id = Column(Integer, primary_key=True)
    district_id = Column(Integer, ForeignKey("district.district_id"))
    flood_inundation = Column(Float)
    stagnant_water_duration = Column(Float)   # we rename later
    mean_ndvi = Column(Float)
    week_id = Column(Integer, ForeignKey("week.week_id"))