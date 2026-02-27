"""
PropList Seed Script v3
Creates admin user + 10 sample properties with 6 photos each.
Idempotent — safe to run multiple times.
Run: python seed.py
"""
import asyncio
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.session import AsyncSessionLocal
from models.user import User
from models.property import Property
from models.property_image import PropertyImage
from services.auth_service import hash_password
from services.image_service import IMAGE_LABELS, seed_images_for_property

# ── Credentials ───────────────────────────────────────────────────────────────
ADMIN_EMAIL    = "admin@proplist.com"
ADMIN_PASSWORD = "Admin@1234"
ADMIN_NAME     = "PropList Admin"

# ── Image Map ────────────────────────────────────────────────────────────────
# Shared room images mapped by label
ROOM_IMGS = {
    "Exterior":     ["sample_apartment.jpg", "sample_villa.jpg", "sample_house.jpg",
                     "sample_commercial.jpg", "img_exterior_duplex.jpg"],
    "Living Room":  ["img_living_luxury.jpg", "img_living_cozy.jpg"],
    "Kitchen":      ["img_kitchen_modern.jpg", "img_kitchen_villa.jpg"],
    "Bedroom":      ["img_bedroom_luxury.jpg", "img_bedroom_cozy.jpg"],
    "Bathroom":     ["img_bathroom_luxury.jpg", "img_bathroom_modern.jpg"],
    "View":         ["img_balcony_sea.jpg", "img_balcony_garden.jpg"],
}

def img_set(exterior_idx: int, living_idx: int = 0, kitchen_idx: int = 0,
            bedroom_idx: int = 0, bathroom_idx: int = 0, view_idx: int = 0) -> list:
    """Build a 6-image list (one per label)."""
    ext   = ROOM_IMGS["Exterior"][min(exterior_idx, len(ROOM_IMGS["Exterior"]) - 1)]
    liv   = ROOM_IMGS["Living Room"][min(living_idx, 1)]
    kit   = ROOM_IMGS["Kitchen"][min(kitchen_idx, 1)]
    bed   = ROOM_IMGS["Bedroom"][min(bedroom_idx, 1)]
    bath  = ROOM_IMGS["Bathroom"][min(bathroom_idx, 1)]
    view  = ROOM_IMGS["View"][min(view_idx, 1)]
    return [
        {"filename": ext,  "label": "Exterior"},
        {"filename": liv,  "label": "Living Room"},
        {"filename": kit,  "label": "Kitchen"},
        {"filename": bed,  "label": "Bedroom"},
        {"filename": bath, "label": "Bathroom"},
        {"filename": view, "label": "View"},
    ]


# ── 10 Sample Properties ──────────────────────────────────────────────────────
PROPERTIES = [
    {
        "title": "Luxury Sea-Facing 3BHK in Bandra West",
        "description": "Stunning sea-facing apartment with floor-to-ceiling windows, modular kitchen, and top-class amenities including rooftop pool and gym. Prime Bandra location with excellent connectivity to schools, malls and restaurants.",
        "city": "Mumbai",
        "address": "12, Sea View Heights, Bandra West, Mumbai 400050",
        "price": 18500000,
        "bedrooms": 3, "bathrooms": 2,
        "property_type": "apartment",
        "image_filename": "sample_apartment.jpg",
        "images": img_set(0, 0, 0, 0, 0, 0),
    },
    {
        "title": "Elegant 4BHK Villa with Private Pool — Prestige Layout",
        "description": "Beautiful villa nestled in a serene gated community with lush tropical garden, private infinity swimming pool, and smart home automation. 24/7 security, clubhouse and children's play area.",
        "city": "Bangalore",
        "address": "Plot 5, Prestige Lake Ridge, Kanakpura Road, Bangalore 560083",
        "price": 32000000,
        "bedrooms": 4, "bathrooms": 3,
        "property_type": "villa",
        "image_filename": "sample_villa.jpg",
        "images": img_set(1, 0, 1, 0, 0, 1),
    },
    {
        "title": "Charming 3BHK Independent House with Garden",
        "description": "Warm and inviting independent house with terracotta tiled roof, spacious garden, car parking, and quiet residential street. Great for families looking for privacy and space.",
        "city": "Pune",
        "address": "78, Bougainvillea Lane, Aundh, Pune 411007",
        "price": 9500000,
        "bedrooms": 3, "bathrooms": 2,
        "property_type": "house",
        "image_filename": "sample_house.jpg",
        "images": img_set(2, 1, 0, 1, 1, 1),
    },
    {
        "title": "Modern Grade-A Commercial Office in Connaught Place",
        "description": "Premium open-plan office with panoramic city skyline views, glass partitions, ergonomic furniture and high-speed fibre. Ideal for tech startups and large corporates. LEED certified building.",
        "city": "Delhi",
        "address": "Level 8, Tower B, Statesman Business Hub, Connaught Place, New Delhi 110001",
        "price": 22000000,
        "bedrooms": 0, "bathrooms": 4,
        "property_type": "commercial",
        "image_filename": "sample_commercial.jpg",
        "images": img_set(3, 0, 0, 0, 1, 0),
    },
    {
        "title": "Prime DTCP-Approved Residential Corner Plot",
        "description": "DTCP approved corner plot in a fast-growing layout with wide roads, electricity and drinking water connections. Clear title documents available. East-facing, surrounded by premium residential projects.",
        "city": "Hyderabad",
        "address": "Plot 22, Celestial Enclave, Kompally, Hyderabad 500014",
        "price": 4800000,
        "bedrooms": 0, "bathrooms": 0,
        "property_type": "plot",
        "image_filename": "sample_plot.jpg",
        "images": [
            {"filename": "sample_plot.jpg",        "label": "Exterior"},
            {"filename": "img_balcony_garden.jpg",  "label": "View"},
            {"filename": "sample_apartment.jpg",    "label": "Nearby Building"},
            {"filename": "img_living_cozy.jpg",     "label": "Sample Interior"},
            {"filename": "img_kitchen_modern.jpg",  "label": "Sample Kitchen"},
            {"filename": "img_bedroom_cozy.jpg",    "label": "Sample Bedroom"},
        ],
    },
    {
        "title": "Stylish Studio Apartment near Marina Beach",
        "description": "Contemporary studio with sea breeze and large windows. Fully furnished with modular kitchen and built-in storage. Walking distance to Marina Beach, restaurants and Chennai metro.",
        "city": "Chennai",
        "address": "301, Tidel Heights, Besant Nagar, Chennai 600090",
        "price": 3200000,
        "bedrooms": 1, "bathrooms": 1,
        "property_type": "apartment",
        "image_filename": "sample_studio.jpg",
        "images": img_set(0, 1, 0, 1, 1, 0),
    },
    {
        "title": "Beachfront Penthouse — Calangute, North Goa",
        "description": "Rare beachfront penthouse with private rooftop terrace, plunge pool, panoramic Arabian Sea views and bespoke interiors. Perfect for luxury living or high-yield holiday rentals. Fully managed option available.",
        "city": "Goa",
        "address": "Penthouse, Azul Tower, Calangute Beach Road, North Goa 403516",
        "price": 55000000,
        "bedrooms": 3, "bathrooms": 3,
        "property_type": "villa",
        "image_filename": "img_exterior_penthouse.jpg",
        "images": img_set(4, 0, 1, 0, 0, 0),
    },
    {
        "title": "Heritage Colonial Bungalow — Chamundi Hills",
        "description": "Rare 100-year-old colonial bungalow spread across a half-acre estate on Chamundi Hills. Teak wood floors, arched verandas, lush garden with mango trees. Meticulously restored with modern plumbing and wiring.",
        "city": "Mysore",
        "address": "8, Chamundi Hill Road, Mysore 570010",
        "price": 14500000,
        "bedrooms": 4, "bathrooms": 3,
        "property_type": "house",
        "image_filename": "img_living_cozy.jpg",
        "images": img_set(2, 1, 1, 1, 1, 1),
    },
    {
        "title": "Sleek Modern Duplex with Rooftop Lounge — Sector 50",
        "description": "Award-winning contemporary duplex with double-height living room, open-plan kitchen, rooftop lounge with city panorama and private parking for 2 cars. Gated premium society, 5 min from Delhi Metro.",
        "city": "Noida",
        "address": "G-204, Emerald Hills, Sector 50, Noida 201301",
        "price": 12500000,
        "bedrooms": 3, "bathrooms": 3,
        "property_type": "house",
        "image_filename": "img_exterior_duplex.jpg",
        "images": img_set(4, 0, 0, 0, 1, 0),
    },
    {
        "title": "Panoramic 2BHK High-Rise — Hiranandani Gardens",
        "description": "Light-flooded corner apartment on the 22nd floor with 270° city and lake views. Premium fittings, modular kitchen, Italian marble flooring and balcony with breathtaking sunsets.",
        "city": "Mumbai",
        "address": "2204, Tower E, Hiranandani Gardens, Powai, Mumbai 400076",
        "price": 7800000,
        "bedrooms": 2, "bathrooms": 2,
        "property_type": "apartment",
        "image_filename": "sample_apartment.jpg",
        "images": img_set(0, 0, 0, 1, 0, 0),
    },
]


# ── Main Seed ─────────────────────────────────────────────────────────────────
async def seed():
    async with AsyncSessionLocal() as db:

        # Skip seeding if data already exists (protects real user data)
        result = await db.execute(select(User))
        if result.scalars().first() is not None:
            print("⏭️  Data already exists — skipping seed.")
            return

        # 1. Admin user
        admin = User(
            id=uuid.uuid4(),
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_NAME,
            role="admin",
        )
        db.add(admin)
        await db.flush()
        await db.refresh(admin)
        print(f"✅ Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

        # 2. Properties with images
        for data in PROPERTIES:
            images_spec = data.pop("images")
            prop = Property(
                id=uuid.uuid4(),
                owner_id=admin.id,
                **data,
            )
            db.add(prop)
            await db.flush()

            await seed_images_for_property(db, str(prop.id), images_spec)
            print(f"  ✅ {prop.title[:55]} — {len(images_spec)} photos")

        await db.commit()

        print(f"""
🎉 Seed complete!
   ├─ Admin:     {ADMIN_EMAIL} / {ADMIN_PASSWORD}
   ├─ Properties: {len(PROPERTIES)}
   └─ Photos per property: 6

   Admin Panel  → http://localhost:8000/admin
   Site         → http://localhost:8000/properties
""")


if __name__ == "__main__":
    asyncio.run(seed())
