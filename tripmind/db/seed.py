"""Database Seeder: Populates PostgreSQL with verified travel data for Kashmir, Goa, and Assam."""

import logging
from tripmind.db.session import engine, Base, SessionLocal
from tripmind.db.models import RegionModel, AccommodationModel, ActivityModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tripmind.seed")

REGIONS_DATA = [
    # Kashmir
    {
        "destination": "Kashmir",
        "region_name": "Srinagar",
        "is_accessible": True,
        "status_note": "Open and accessible in winter. Dal Lake experiences morning mist. Sunset at 5:15 PM.",
        "temp_range_celsius": "-2°C to 10°C",
        "daylight_hours": "9.5 hours",
        "sunset_time": "5:15 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Dal Lake", "Mughal Gardens", "Old Srinagar Heritage Alley"],
    },
    {
        "destination": "Kashmir",
        "region_name": "Gulmarg",
        "is_accessible": True,
        "status_note": "Open alpine snow meadow. Tangmarg-to-Gulmarg requires mandatory 4x4 snow-chain cabs.",
        "temp_range_celsius": "-8°C to 2°C",
        "daylight_hours": "9.5 hours",
        "sunset_time": "5:15 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Gondola Phase 1 Viewpoint", "Snow pine forests", "St. Mary's Church"],
    },
    {
        "destination": "Kashmir",
        "region_name": "Pahalgam",
        "is_accessible": True,
        "status_note": "Open valley along Lidder river. Calm and picturesque in winter.",
        "temp_range_celsius": "-5°C to 6°C",
        "daylight_hours": "9.5 hours",
        "sunset_time": "5:20 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Betaab Valley", "Aru Valley pine trails", "Lidder River"],
    },
    {
        "destination": "Kashmir",
        "region_name": "Sonamarg",
        "is_accessible": False,
        "status_note": "CLOSED: Highway closed due to heavy snow accumulation and avalanche hazards in December.",
        "temp_range_celsius": "-12°C to -2°C",
        "daylight_hours": "9.5 hours",
        "sunset_time": "5:10 PM",
        "recommended_stay_nights": 0,
        "scenic_highlights": ["Thajiwas Glacier (Inaccessible)"],
    },
    # Goa
    {
        "destination": "Goa",
        "region_name": "North Goa",
        "is_accessible": True,
        "status_note": "Vibrant beach season. Historic Portuguese quarters and beach shacks active.",
        "temp_range_celsius": "22°C to 32°C",
        "daylight_hours": "11.5 hours",
        "sunset_time": "6:05 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Vagator cliffs", "Fontainhas Latin Quarter", "Chapora river"],
    },
    {
        "destination": "Goa",
        "region_name": "South Goa",
        "is_accessible": True,
        "status_note": "Relaxing and serene. White sand beaches, coconut groves, and backwaters.",
        "temp_range_celsius": "21°C to 31°C",
        "daylight_hours": "11.5 hours",
        "sunset_time": "6:08 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Palolem Beach bay", "Cabo de Rama viewpoint", "Sal River"],
    },
    # Assam
    {
        "destination": "Assam",
        "region_name": "Guwahati",
        "is_accessible": True,
        "status_note": "Gateway to the Northeast on the Brahmaputra River. Pleasant dry winter season. Early eastern sunset at 4:48 PM.",
        "temp_range_celsius": "17°C to 27°C",
        "daylight_hours": "10.5 hours",
        "sunset_time": "4:48 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Brahmaputra Riverfront", "Guwahati Ropeway", "Umananda Peacock Island"],
    },
    {
        "destination": "Assam",
        "region_name": "Kaziranga",
        "is_accessible": True,
        "status_note": "Open for winter wildlife jeep safaris. Located 4.5 hours from Guwahati.",
        "temp_range_celsius": "14°C to 25°C",
        "daylight_hours": "10.5 hours",
        "sunset_time": "4:45 PM",
        "recommended_stay_nights": 2,
        "scenic_highlights": ["Central Range Kohora", "Bagori Western Range", "Orchid & Biodiversity Park"],
    },
]

ACCOMMODATIONS_DATA = [
    # Kashmir
    {
        "region": "Srinagar",
        "name": "The Chinar Resort & Spa",
        "rating": 4.7,
        "price_per_night_inr": 7500.0,
        "heating_verified": True,
        "amenities": ["central_heating", "electric_blanket", "hot_water_24x7", "mountain_view"],
        "couple_suitability": "Romantic boutique resort, insulated heated rooms, quiet luxury.",
        "address_or_area": "Harwan, Srinagar",
    },
    {
        "region": "Srinagar",
        "name": "Mascot Luxury Houseboat",
        "rating": 4.6,
        "price_per_night_inr": 6500.0,
        "heating_verified": True,
        "amenities": ["wood_bukhari_heating", "electric_blanket", "dal_lake_view"],
        "couple_suitability": "Classic wooden cedar houseboat on Nigeen Lake, cozy and atmospheric.",
        "address_or_area": "Nigeen Lake, West Bank, Srinagar",
    },
    {
        "region": "Gulmarg",
        "name": "Hotel Highlands Park",
        "rating": 4.6,
        "price_per_night_inr": 8500.0,
        "heating_verified": True,
        "amenities": ["central_heating", "electric_blanket", "classic_heritage_fireplace"],
        "couple_suitability": "Vintage alpine cottage retreat, heritage couple ambiance.",
        "address_or_area": "Circular Road, Gulmarg",
    },
    {
        "region": "Gulmarg",
        "name": "Nedous Hotel",
        "rating": 4.4,
        "price_per_night_inr": 7800.0,
        "heating_verified": True,
        "amenities": ["bukhari_heating", "electric_blanket", "heritage_architecture"],
        "couple_suitability": "Cozy historic alpine retreat amidst pine meadows.",
        "address_or_area": "Gulmarg Meadow",
    },
    {
        "region": "Pahalgam",
        "name": "Pahalgam Hotel",
        "rating": 4.6,
        "price_per_night_inr": 8200.0,
        "heating_verified": True,
        "amenities": ["central_heating", "electric_blanket", "lidder_river_view"],
        "couple_suitability": "Serene riverside stay with reliable heating.",
        "address_or_area": "Main Market, Lidder Banks, Pahalgam",
    },
    # Goa
    {
        "region": "North Goa",
        "name": "Ahilya by the Sea",
        "rating": 4.8,
        "price_per_night_inr": 14000.0,
        "heating_verified": False,
        "amenities": ["ac", "infinity_pool", "sea_facing", "boutique_gardens"],
        "couple_suitability": "Intimate luxury haven on dolphin bay.",
        "address_or_area": "Nerul, North Goa",
    },
    {
        "region": "South Goa",
        "name": "Heritage Village Resort & Spa",
        "rating": 4.7,
        "price_per_night_inr": 6800.0,
        "heating_verified": False,
        "amenities": ["ac", "swimming_pool", "ayurvedic_spa", "beach_walk_5min"],
        "couple_suitability": "Serene Portuguese estate, lush lawns, peaceful beach.",
        "address_or_area": "Arossim Beach, South Goa",
    },
    # Assam
    {
        "region": "Guwahati",
        "name": "Vivanta Guwahati",
        "rating": 4.7,
        "price_per_night_inr": 6200.0,
        "heating_verified": False,
        "amenities": ["ac", "tea_lounge", "spa", "authentic_dining", "swimming_pool"],
        "couple_suitability": "Tranquil luxury resort surrounded by tea gardens and hills.",
        "address_or_area": "Khanapara, GS Road, Guwahati",
    },
    {
        "region": "Guwahati",
        "name": "Radisson Blu Hotel Guwahati",
        "rating": 4.6,
        "price_per_night_inr": 5800.0,
        "heating_verified": False,
        "amenities": ["ac", "lake_view", "multiple_restaurants", "gym"],
        "couple_suitability": "Comfortable 5-star property situated next to Deepor Beel lake.",
        "address_or_area": "Gotanagar, Maligaon, Guwahati",
    },
    {
        "region": "Kaziranga",
        "name": "Borgos Resort Kaziranga",
        "rating": 4.6,
        "price_per_night_inr": 6500.0,
        "heating_verified": False,
        "amenities": ["ac", "jungle_cottages", "nature_walks", "bonfire"],
        "couple_suitability": "Forest estate next to Kaziranga National Park border.",
        "address_or_area": "Near Central Range Kohora, Kaziranga",
    },
]

ACTIVITIES_DATA = [
    # Kashmir (Scenic & Culinary vs Adventure)
    {
        "region": "Srinagar",
        "name": "Sunset Shikara Ride on Dal Lake",
        "category": "scenic",
        "is_adventure": False,
        "estimated_duration_hours": 2.0,
        "cost_inr": 1500.0,
        "description": "Private covered shikara ride with hot Kangri heater exploring floating gardens during golden hour.",
        "best_time_of_day": "3:00 PM - 5:00 PM",
    },
    {
        "region": "Srinagar",
        "name": "Traditional Wazwan Feast at Ahdoos",
        "category": "culinary",
        "is_adventure": False,
        "estimated_duration_hours": 1.5,
        "cost_inr": 1800.0,
        "description": "Multi-course Kashmiri Wazwan: Rogan Josh, Rista, Gushtaba, and saffron Phirni.",
        "best_time_of_day": "Dinner",
    },
    {
        "region": "Srinagar",
        "name": "Chai Jaai Tea Room & Saffron Scented Kahwa",
        "category": "culinary",
        "is_adventure": False,
        "estimated_duration_hours": 1.0,
        "cost_inr": 600.0,
        "description": "Artisanal tea room on the Jhelum bund serving Kashmiri Kahwa with crushed almonds.",
        "best_time_of_day": "Morning or 4:00 PM",
    },
    {
        "region": "Gulmarg",
        "name": "Gulmarg Gondola Ride (Phase 1 to Kongdoori)",
        "category": "scenic",
        "is_adventure": False,
        "estimated_duration_hours": 2.5,
        "cost_inr": 1700.0,
        "description": "Enclosed cable car ascent to Kongdoori bowl for panoramic snow-capped views. High-altitude skiing excluded.",
        "best_time_of_day": "10:30 AM",
    },
    {
        "region": "Gulmarg",
        "name": "Extreme Off-Piste Snow Skiing",
        "category": "adventure",
        "is_adventure": True,  # ADVENTURE
        "estimated_duration_hours": 4.0,
        "cost_inr": 6500.0,
        "description": "Downhill skiing on powder snow from 13,780 feet.",
        "best_time_of_day": "Morning",
    },
    {
        "region": "Gulmarg",
        "name": "Snowmobile Thrill Ride",
        "category": "adventure",
        "is_adventure": True,  # ADVENTURE
        "estimated_duration_hours": 1.5,
        "cost_inr": 3000.0,
        "description": "High-powered motorized snow bike riding across deep trails.",
        "best_time_of_day": "Afternoon",
    },
    # Goa
    {
        "region": "North Goa",
        "name": "Fontainhas Portuguese Heritage & Bakeries",
        "category": "culinary",
        "is_adventure": False,
        "estimated_duration_hours": 2.5,
        "cost_inr": 800.0,
        "description": "Walk along pastel-colored Latin Quarter streets, tasting Bebinca and Goan poee.",
        "best_time_of_day": "Morning",
    },
    {
        "region": "South Goa",
        "name": "Palolem Bay Sunset Dolphin Boat & Fresh Seafood",
        "category": "scenic",
        "is_adventure": False,
        "estimated_duration_hours": 2.0,
        "cost_inr": 1200.0,
        "description": "Gentle wooden boat ride watching coastal dolphins, followed by butter garlic crab.",
        "best_time_of_day": "Late Afternoon",
    },
    {
        "region": "North Goa",
        "name": "Parasailing & Jet Ski Sports",
        "category": "adventure",
        "is_adventure": True,  # ADVENTURE
        "estimated_duration_hours": 1.5,
        "cost_inr": 2500.0,
        "description": "High-speed water sports.",
        "best_time_of_day": "Morning",
    },
    # Assam
    {
        "region": "Guwahati",
        "name": "Traditional Assamese Khaar & Thali at Paradise Restaurant",
        "category": "culinary",
        "is_adventure": False,
        "estimated_duration_hours": 1.5,
        "cost_inr": 1200.0,
        "description": "Authentic Parampara Thali: Khar (alkaline papaya), Masor Tenga (tangy river fish curry), Joha rice, and Payas.",
        "best_time_of_day": "Lunch",
    },
    {
        "region": "Guwahati",
        "name": "Sunset Brahmaputra River Cruise (Alfresco Grand)",
        "category": "scenic",
        "is_adventure": False,
        "estimated_duration_hours": 2.0,
        "cost_inr": 1500.0,
        "description": "Gentle cruise on the Brahmaputra river watching the golden 4:48 PM sunset with live Assamese folk flute.",
        "best_time_of_day": "3:30 PM - 5:30 PM",
    },
    {
        "region": "Guwahati",
        "name": "Ethnic Smoked Duck & Bamboo Shoot Dining at Khorikaa",
        "category": "culinary",
        "is_adventure": False,
        "estimated_duration_hours": 1.5,
        "cost_inr": 1400.0,
        "description": "Specialty bamboo hollow smoked duck curry, roasted sesame pork, and fresh local herb chutneys.",
        "best_time_of_day": "Dinner",
    },
    {
        "region": "Guwahati",
        "name": "Guwahati Aerial Ropeway to Peacock Island",
        "category": "scenic",
        "is_adventure": False,
        "estimated_duration_hours": 1.5,
        "cost_inr": 300.0,
        "description": "Scenic cable car glide over the Brahmaputra offering panoramic aerial views of river sandbars.",
        "best_time_of_day": "Morning (11:00 AM)",
    },
    {
        "region": "Guwahati",
        "name": "Brahmaputra White Water River Rafting",
        "category": "adventure",
        "is_adventure": True,  # ADVENTURE
        "estimated_duration_hours": 3.0,
        "cost_inr": 3500.0,
        "description": "High-adrenaline rapid river rafting.",
        "best_time_of_day": "Morning",
    },
]


def seed_database():
    """Create tables and seed initial travel datasets into PostgreSQL."""
    logger.info("Connecting to PostgreSQL and creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Regions
        if db.query(RegionModel).count() == 0:
            logger.info(f"Seeding {len(REGIONS_DATA)} regions...")
            for item in REGIONS_DATA:
                db.add(RegionModel(**item))
            db.commit()

        # 2. Seed Accommodations
        if db.query(AccommodationModel).count() == 0:
            logger.info(f"Seeding {len(ACCOMMODATIONS_DATA)} accommodations...")
            for item in ACCOMMODATIONS_DATA:
                db.add(AccommodationModel(**item))
            db.commit()

        # 3. Seed Activities
        if db.query(ActivityModel).count() == 0:
            logger.info(f"Seeding {len(ACTIVITIES_DATA)} activities...")
            for item in ACTIVITIES_DATA:
                db.add(ActivityModel(**item))
            db.commit()

        logger.info("Database seeding completed successfully!")
    except Exception as e:
        logger.error(f"Error during database seed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
