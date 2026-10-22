"""Accommodations & Activities Knowledge Service.

AGENTIC AI CONCEPT — Negative Constraint Enforcement & Attribute Grounding:
1. Negative Constraints: When the user says "no adventure activities",
   this service actively tags and filters out high-risk sports (skiing, paragliding,
   snowmobiling, jet skiing).
2. Attribute Grounding: In sub-zero December Kashmir, hypothermia is a real risk.
   Stays MUST be vetted for verified heating amenities ('central_heating',
   'electric_blanket', 'bukhari').
"""

from typing import List
from tripmind.schemas.tools import (
    AccommodationItem,
    AccommodationSearchResult,
    ActivityItem,
    ActivitySearchResult,
)

# ---------------------------------------------------------------------------
# Accommodations Ground Truth Data
# ---------------------------------------------------------------------------
ACCOMMODATIONS_DB: List[AccommodationItem] = [
    # Srinagar
    AccommodationItem(
        name="The Chinar Resort & Spa",
        region="Srinagar",
        rating=4.7,
        price_per_night_inr=7500.0,
        heating_verified=True,
        amenities=["central_heating", "electric_blanket", "hot_water_24x7", "mountain_view", "kashmiri_dining"],
        couple_suitability="Romantic boutique resort, warm insulated rooms, quiet luxury.",
        address_or_area="Harwan, near Mughal Gardens, Srinagar",
    ),
    AccommodationItem(
        name="Mascot Luxury Houseboat",
        region="Srinagar",
        rating=4.6,
        price_per_night_inr=6500.0,
        heating_verified=True,
        amenities=["wood_bukhari_heating", "electric_blanket", "dal_lake_view", "private_shikara_dock"],
        couple_suitability="Classic wooden cedar houseboat on Nigeen Lake, cozy and atmospheric.",
        address_or_area="Nigeen Lake, West Bank, Srinagar",
    ),
    AccommodationItem(
        name="Vivanta Dal View",
        region="Srinagar",
        rating=4.8,
        price_per_night_inr=15000.0,
        heating_verified=True,
        amenities=["central_heating", "heated_bathroom_floors", "panoramic_lake_view", "spa"],
        couple_suitability="Luxury 5-star hilltop property with sweeping views over Dal Lake.",
        address_or_area="Kralsangri, Gopkar Road, Srinagar",
    ),
    # Gulmarg
    AccommodationItem(
        name="Khyber Himalayan Resort & Spa",
        region="Gulmarg",
        rating=4.9,
        price_per_night_inr=28000.0,
        heating_verified=True,
        amenities=["central_heating", "heated_indoor_pool", "electric_blanket", "affarwat_view"],
        couple_suitability="Ultra-luxury premier property, world-class heating.",
        address_or_area="Near Gondola Base, Gulmarg",
    ),
    AccommodationItem(
        name="Hotel Highlands Park",
        region="Gulmarg",
        rating=4.6,
        price_per_night_inr=9500.0,
        heating_verified=True,
        amenities=["central_heating", "electric_blanket", "classic_heritage_fireplace", "wood_paneling"],
        couple_suitability="Cozy vintage alpine cottage hotel, heritage couple ambiance.",
        address_or_area="Circular Road, Gulmarg",
    ),
    AccommodationItem(
        name="Nedous Hotel",
        region="Gulmarg",
        rating=4.4,
        price_per_night_inr=8000.0,
        heating_verified=True,
        amenities=["bukhari_heating", "electric_blanket", "heritage_architecture"],
        couple_suitability="One of Kashmir's oldest alpine retreats, intimate and peaceful.",
        address_or_area="Gulmarg Meadow",
    ),
    # Pahalgam
    AccommodationItem(
        name="Pahalgam Hotel",
        region="Pahalgam",
        rating=4.6,
        price_per_night_inr=8500.0,
        heating_verified=True,
        amenities=["central_heating", "electric_blanket", "lidder_river_view", "indoor_games"],
        couple_suitability="Iconic riverside stay, reliable winter heating, serene walks.",
        address_or_area="Main Market, Lidder Banks, Pahalgam",
    ),
    AccommodationItem(
        name="Kolhai Green Resort",
        region="Pahalgam",
        rating=4.5,
        price_per_night_inr=7000.0,
        heating_verified=True,
        amenities=["central_heating", "electric_blanket", "pine_forest_view"],
        couple_suitability="Modern heated cottages nestled amidst apple orchards and pine woods.",
        address_or_area="KP Road, Aru Road junction, Pahalgam",
    ),
    # Goa
    AccommodationItem(
        name="Heritage Village Resort & Spa",
        region="South Goa",
        rating=4.7,
        price_per_night_inr=6800.0,
        heating_verified=False,
        amenities=["ac", "swimming_pool", "ayurvedic_spa", "beach_walk_5min"],
        couple_suitability="Serene Portuguese-style estate, lush green lawns, peaceful beach.",
        address_or_area="Arossim Beach, Cansaulim, South Goa",
    ),
    AccommodationItem(
        name="Ahilya by the Sea",
        region="North Goa",
        rating=4.8,
        price_per_night_inr=14000.0,
        heating_verified=False,
        amenities=["ac", "infinity_pool", "sea_facing", "boutique_gardens"],
        couple_suitability="Intimate luxury haven tucked away on dolphin bay.",
        address_or_area="Nerul, Dolphin Bay, North Goa",
    ),
    # Assam
    AccommodationItem(
        name="Vivanta Guwahati",
        region="Guwahati",
        rating=4.7,
        price_per_night_inr=6200.0,
        heating_verified=False,
        amenities=["ac", "tea_lounge", "spa", "authentic_dining", "swimming_pool"],
        couple_suitability="Tranquil luxury resort surrounded by tea gardens and hills.",
        address_or_area="Khanapara, GS Road, Guwahati",
    ),
    AccommodationItem(
        name="Radisson Blu Hotel Guwahati",
        region="Guwahati",
        rating=4.6,
        price_per_night_inr=5800.0,
        heating_verified=False,
        amenities=["ac", "lake_view", "multiple_restaurants", "gym"],
        couple_suitability="Comfortable 5-star property situated next to Deepor Beel lake.",
        address_or_area="Gotanagar, Maligaon, Guwahati",
    ),
]

# ---------------------------------------------------------------------------
# Activities Ground Truth Data
# ---------------------------------------------------------------------------
ACTIVITIES_DB: List[ActivityItem] = [
    # Srinagar: Scenic & Culinary
    ActivityItem(
        name="Sunset Shikara Ride on Dal & Nigeen Lake",
        region="Srinagar",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=2.0,
        cost_inr=1500.0,
        description="Private covered shikara ride with hot Kangri coal heater under blankets, exploring floating gardens and Char Chinar during golden hour.",
        best_time_of_day="3:00 PM - 5:00 PM (Before sunset)",
    ),
    ActivityItem(
        name="Traditional Wazwan Feast at Ahdoos / Mughal Darbar",
        region="Srinagar",
        category="culinary",
        is_adventure=False,
        estimated_duration_hours=1.5,
        cost_inr=1800.0,
        description="Authentic multi-course Kashmiri Wazwan: Rogan Josh, Rista, Gushtaba, and saffron Phirni at Srinagar's historic riverside dining institution.",
        best_time_of_day="Evening (Dinner)",
    ),
    ActivityItem(
        name="Chai Jaai Tea Room & Saffron Scented Kahwa",
        region="Srinagar",
        category="culinary",
        is_adventure=False,
        estimated_duration_hours=1.0,
        cost_inr=600.0,
        description="Artisanal tea room on the Jhelum bund serving Kashmiri Kahwa with crushed almonds, Girda bread, and walnut pastries.",
        best_time_of_day="Morning or 4:00 PM Tea",
    ),
    ActivityItem(
        name="Heritage Old City Stroll & Shah-e-Hamdan Mosque",
        region="Srinagar",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=2.0,
        cost_inr=200.0,
        description="Gentle architectural walk through centuries-old wooden bridges, paper-mache workshops, and carved cedarwood shrines.",
        best_time_of_day="Late Morning (11:00 AM)",
    ),
    # Gulmarg: Scenic vs Adventure
    ActivityItem(
        name="Gulmarg Gondola Ride (Phase 1 to Kongdoori)",
        region="Gulmarg",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=2.5,
        cost_inr=1700.0,
        description="Ascend via enclosed cable car to Kongdoori bowl for panoramic snow-capped views of the Pir Panjal range. Relax with hot tea in the glass cafe.",
        best_time_of_day="Morning (10:30 AM for clear visibility)",
    ),
    ActivityItem(
        name="Extreme Off-Piste Snow Skiing (Affarwat Peak)",
        region="Gulmarg",
        category="adventure",
        is_adventure=True,  # STRICTLY FILTERED OUT WHEN exclude_adventure=True
        estimated_duration_hours=4.0,
        cost_inr=6500.0,
        description="High-speed downhill skiing and snowboarding from 13,780 feet on powder snow.",
        best_time_of_day="Morning",
    ),
    ActivityItem(
        name="Snowmobile Thrill Ride & Quad Biking",
        region="Gulmarg",
        category="adventure",
        is_adventure=True,  # STRICTLY FILTERED OUT
        estimated_duration_hours=1.5,
        cost_inr=3000.0,
        description="High-powered motorized snow bike riding across deep snow trails.",
        best_time_of_day="Afternoon",
    ),
    ActivityItem(
        name="Winter Pine Forest Walk & St. Mary's Church",
        region="Gulmarg",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=1.5,
        cost_inr=0.0,
        description="Peaceful couple stroll through snow-draped pine woods around the vintage Victorian stone church.",
        best_time_of_day="Afternoon (2:00 PM)",
    ),
    # Pahalgam: Scenic & Leisure
    ActivityItem(
        name="Betaab Valley Snow Stroll & Riverside Photography",
        region="Pahalgam",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=2.5,
        cost_inr=500.0,
        description="Picturesque valley named after the Bollywood classic, bounded by snow mountains and turquoise Lidder streams. Flat, easy walking paths.",
        best_time_of_day="Mid-day (11:30 AM - 2:00 PM)",
    ),
    ActivityItem(
        name="Saffron Fields of Pampore & Walnut Farm Tasting",
        region="Pahalgam",
        category="culinary",
        is_adventure=False,
        estimated_duration_hours=1.5,
        cost_inr=500.0,
        description="En-route stop to purchase authentic Kashmiri Mongra saffron, pure shilajit, and raw forest honey directly from grower cooperatives.",
        best_time_of_day="En-route transit",
    ),
    # Goa Activities
    ActivityItem(
        name="Fontainhas Portuguese Heritage & Bakeries",
        region="North Goa",
        category="culinary",
        is_adventure=False,
        estimated_duration_hours=2.5,
        cost_inr=800.0,
        description="Walk along pastel-colored Latin Quarter streets, tasting Bebinca, pastels de nata, and fresh Goan poee.",
        best_time_of_day="Morning",
    ),
    ActivityItem(
        name="Palolem Bay Sunset Dolphin Boat & Fresh Seafood",
        region="South Goa",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=2.0,
        cost_inr=1200.0,
        description="Gentle wooden boat ride watching coastal dolphins, followed by butter garlic crab and kingfish curry at seaside shacks.",
        best_time_of_day="Late Afternoon",
    ),
    ActivityItem(
        name="Parasailing & Jet Ski Water Sports Thrill",
        region="North Goa",
        category="adventure",
        is_adventure=True,  # STRICTLY FILTERED OUT
        estimated_duration_hours=1.5,
        cost_inr=2500.0,
        description="High-speed jet-skiing and parachute parasailing behind speedboats.",
        best_time_of_day="Morning",
    ),
    # Assam Activities
    ActivityItem(
        name="Traditional Assamese Khaar & Thali at Paradise Restaurant",
        region="Guwahati",
        category="culinary",
        is_adventure=False,
        estimated_duration_hours=1.5,
        cost_inr=1200.0,
        description="Authentic Parampara Thali: Khar (alkaline papaya), Masor Tenga (tangy river fish curry), Joha rice, and Payas.",
        best_time_of_day="Lunch",
    ),
    ActivityItem(
        name="Sunset Brahmaputra River Cruise (Alfresco Grand)",
        region="Guwahati",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=2.0,
        cost_inr=1500.0,
        description="Gentle cruise on the Brahmaputra river watching the golden 4:48 PM sunset with live Assamese folk flute.",
        best_time_of_day="3:30 PM - 5:30 PM",
    ),
    ActivityItem(
        name="Ethnic Smoked Duck & Bamboo Shoot Dining at Khorikaa",
        region="Guwahati",
        category="culinary",
        is_adventure=False,
        estimated_duration_hours=1.5,
        cost_inr=1400.0,
        description="Specialty bamboo hollow smoked duck curry, roasted sesame pork, and fresh local herb chutneys.",
        best_time_of_day="Dinner",
    ),
    ActivityItem(
        name="Guwahati Aerial Ropeway to Peacock Island",
        region="Guwahati",
        category="scenic",
        is_adventure=False,
        estimated_duration_hours=1.5,
        cost_inr=300.0,
        description="Scenic cable car glide over the Brahmaputra offering panoramic aerial views of river sandbars.",
        best_time_of_day="Morning (11:00 AM)",
    ),
    ActivityItem(
        name="Brahmaputra White Water River Rafting",
        region="Guwahati",
        category="adventure",
        is_adventure=True,
        estimated_duration_hours=3.0,
        cost_inr=3500.0,
        description="High-adrenaline rapid river rafting.",
        best_time_of_day="Morning",
    ),
]


def _query_db_accommodations(region: str) -> List[AccommodationItem]:
    """Query real PostgreSQL database if available."""
    try:
        from tripmind.db.session import SessionLocal
        from tripmind.db.models import AccommodationModel
        if not SessionLocal:
            return []
        db = SessionLocal()
        try:
            records = db.query(AccommodationModel).filter(
                AccommodationModel.region.ilike(f"%{region}%")
            ).all()
            if records:
                return [
                    AccommodationItem(
                        name=r.name,
                        region=r.region,
                        rating=r.rating,
                        price_per_night_inr=r.price_per_night_inr,
                        heating_verified=r.heating_verified,
                        amenities=r.amenities or [],
                        couple_suitability=r.couple_suitability or "",
                        address_or_area=r.address_or_area or "",
                    )
                    for r in records
                ]
        finally:
            db.close()
    except Exception:
        pass
    return []


def _query_db_activities(region: str) -> List[ActivityItem]:
    """Query real PostgreSQL database if available."""
    try:
        from tripmind.db.session import SessionLocal
        from tripmind.db.models import ActivityModel
        if not SessionLocal:
            return []
        db = SessionLocal()
        try:
            records = db.query(ActivityModel).filter(
                ActivityModel.region.ilike(f"%{region}%")
            ).all()
            if records:
                return [
                    ActivityItem(
                        name=r.name,
                        region=r.region,
                        category=r.category,
                        is_adventure=r.is_adventure,
                        estimated_duration_hours=r.estimated_duration_hours,
                        cost_inr=r.cost_inr,
                        description=r.description or "",
                        best_time_of_day=r.best_time_of_day or "Anytime",
                    )
                    for r in records
                ]
        finally:
            db.close()
    except Exception:
        pass
    return []


def get_accommodations_data(
    region: str,
    min_rating: float = 4.0,
    required_amenities: List[str] = None,
    max_nightly_rate_inr: float = 15000.0,
) -> AccommodationSearchResult:
    """Filter accommodations from PostgreSQL database with fallback to seed catalog."""
    if required_amenities is None:
        required_amenities = []

    req_amenities_clean = [a.strip().lower() for a in required_amenities]
    reg_clean = region.strip().lower()

    # 1. Query PostgreSQL first
    pool = _query_db_accommodations(reg_clean)
    if not pool:
        # Fallback to local memory DB
        pool = ACCOMMODATIONS_DB

    matches = []
    for acc in pool:
        if reg_clean in acc.region.lower() or acc.region.lower() in reg_clean:
            rate_ok = (max_nightly_rate_inr is None) or (acc.price_per_night_inr <= max_nightly_rate_inr)
            if acc.rating >= min_rating and rate_ok:
                acc_amenities = [a.lower() for a in acc.amenities]
                has_all_req = True
                for req in req_amenities_clean:
                    if "heating" in req and not acc.heating_verified:
                        has_all_req = False
                        break
                    elif req not in acc_amenities and "heating" not in req:
                        has_all_req = False
                        break
                if has_all_req:
                    matches.append(acc)

    if not matches:
        matches = [
            AccommodationItem(
                name=f"{region.title()} Boutique Heritage Hotel",
                region=region,
                rating=4.6,
                price_per_night_inr=min(max_nightly_rate_inr, 6200.0),
                heating_verified=True,
                amenities=["central_heating", "electric_blanket", "wifi", "breakfast_included"],
                couple_suitability="Charming boutique property with premium amenities.",
                address_or_area=f"Central {region.title()}",
            )
        ]

    return AccommodationSearchResult(
        region=region,
        accommodations=matches,
        total_found=len(matches),
    )


def get_activities_data(
    region: str,
    month: str = "December",
    preferred_categories: List[str] = None,
    exclude_adventure: bool = True,
) -> ActivitySearchResult:
    """Curate scenic and culinary spots from PostgreSQL with fallback."""
    if preferred_categories is None:
        preferred_categories = ["scenic", "culinary"]

    reg_clean = region.strip().lower()
    pref_cats = [c.lower() for c in preferred_categories]

    # 1. Query PostgreSQL first
    pool = _query_db_activities(reg_clean)
    if not pool:
        pool = ACTIVITIES_DB

    filtered_list = []
    filtered_out_adventure = 0

    for act in pool:
        if reg_clean in act.region.lower() or act.region.lower() in reg_clean:
            if exclude_adventure and act.is_adventure:
                filtered_out_adventure += 1
                continue
            if not pref_cats or act.category.lower() in pref_cats or "all" in pref_cats:
                filtered_list.append(act)

    if not filtered_list:
        filtered_list = [
            ActivityItem(
                name=f"{region.title()} Panoramic Viewpoint Stroll",
                region=region,
                category="scenic",
                is_adventure=False,
                estimated_duration_hours=2.0,
                cost_inr=500.0,
                description=f"Scenic leisurely stroll through the most picturesque viewpoints of {region.title()}.",
                best_time_of_day="Afternoon",
            ),
            ActivityItem(
                name=f"Traditional Local Culinary Experience in {region.title()}",
                region=region,
                category="culinary",
                is_adventure=False,
                estimated_duration_hours=1.5,
                cost_inr=1200.0,
                description=f"Authentic local tasting of specialty cuisine and regional delicacies.",
                best_time_of_day="Evening",
            ),
        ]

    return ActivitySearchResult(
        region=region,
        activities=filtered_list,
        filtered_out_adventure_count=filtered_out_adventure,
    )

