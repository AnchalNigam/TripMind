"""SQLAlchemy ORM models for travel data in PostgreSQL."""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON
from tripmind.db.session import Base


class RegionModel(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(100), index=True, nullable=False)
    region_name = Column(String(100), index=True, nullable=False)
    is_accessible = Column(Boolean, default=True)
    status_note = Column(Text, nullable=False)
    temp_range_celsius = Column(String(50))
    daylight_hours = Column(String(50))
    sunset_time = Column(String(50))
    recommended_stay_nights = Column(Integer, default=2)
    scenic_highlights = Column(JSON, default=list)


class AccommodationModel(Base):
    __tablename__ = "accommodations"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(100), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    rating = Column(Float, default=4.5)
    price_per_night_inr = Column(Float, nullable=False)
    heating_verified = Column(Boolean, default=False)
    amenities = Column(JSON, default=list)
    couple_suitability = Column(Text)
    address_or_area = Column(Text)


class ActivityModel(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(100), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50), index=True, nullable=False)  # scenic, culinary, cultural, adventure
    is_adventure = Column(Boolean, default=False, index=True)
    estimated_duration_hours = Column(Float, default=2.0)
    cost_inr = Column(Float, default=0.0)
    description = Column(Text)
    best_time_of_day = Column(String(100))
