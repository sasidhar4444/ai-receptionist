"""Aria Kitchen seed data — realistic restaurant for prototype testing."""
import asyncio
import json
from datetime import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, engine
from app.db.models import (
    Base, DayOfWeek, KnowledgeDocument, MenuItem,
    Restaurant, RestaurantHour, RestaurantPolicy,
    RestaurantTable, TableStatus,
)


# ─── Restaurant ───────────────────────────────────────────────────────────
RESTAURANT = {
    "name": "Aria Kitchen",
    "address": "42 Bougainvillea Lane, Koramangala, Bengaluru 560034",
    "phone": "+91-80-4567-8900",
    "timezone": "Asia/Kolkata",
    "description": (
        "Aria Kitchen is a contemporary fine-dining restaurant offering a curated menu "
        "of modern Indian and Mediterranean cuisine. Known for its warm ambience, "
        "seasonal ingredients, and impeccable service, Aria Kitchen is the perfect "
        "destination for an intimate dinner, a family celebration, or a business lunch."
    ),
}

# ─── Hours ────────────────────────────────────────────────────────────────
HOURS = [
    {"day_of_week": "monday",    "open_at": time(12, 0), "close_at": time(15, 0),  "is_closed": False},
    {"day_of_week": "monday",    "open_at": time(19, 0), "close_at": time(23, 0),  "is_closed": False},
    {"day_of_week": "tuesday",   "open_at": time(12, 0), "close_at": time(23, 0),  "is_closed": False},
    {"day_of_week": "wednesday", "open_at": time(12, 0), "close_at": time(23, 0),  "is_closed": False},
    {"day_of_week": "thursday",  "open_at": time(12, 0), "close_at": time(23, 0),  "is_closed": False},
    {"day_of_week": "friday",    "open_at": time(12, 0), "close_at": time(23, 30), "is_closed": False},
    {"day_of_week": "saturday",  "open_at": time(11, 0), "close_at": time(23, 30), "is_closed": False},
    {"day_of_week": "sunday",    "open_at": time(11, 0), "close_at": time(22, 0),  "is_closed": False},
]

# ─── Policies ─────────────────────────────────────────────────────────────
POLICIES = [
    ("reservation_policy",   "We do not accept reservations. Aria Kitchen is a walk-in only restaurant. Please arrive and our receptionist will seat you based on current availability."),
    ("children_policy",      "Children of all ages are welcome. We have high chairs available for infants and toddlers. Please let our receptionist know when you arrive."),
    ("pet_policy",           "We love animals but pets are not permitted inside the restaurant. However, leashed dogs are welcome in our outdoor terrace seating area."),
    ("parking",              "Complimentary valet parking is available at the main entrance. Self-parking is also available in the adjoining basement (Rs 50 per hour). Street parking is available nearby."),
    ("payment_methods",      "We accept all major credit and debit cards (Visa, Mastercard, Amex), UPI payments (Google Pay, PhonePe, Paytm), and cash. We do not accept foreign currency."),
    ("accessibility",        "Aria Kitchen is fully wheelchair accessible. We have ramp access, wide aisles, and an accessible restroom. Please inform us of any specific requirements."),
    ("outside_food_policy",  "Outside food and beverages are not permitted on the premises. We can accommodate dietary restrictions — please inform our team in advance."),
    ("waiting_policy",       "During busy periods, you may be asked to wait. Our receptionist will give you a current estimated wait time. We do not hold tables without the full party present."),
    ("dress_code",           "Smart casual attire is recommended. We ask guests to avoid beachwear, flip-flops, or sportswear in the dining room. The outdoor terrace has a relaxed dress code."),
    ("corkage_policy",       "We do not offer a corkage policy. Our curated wine list and cocktail menu are available to complement your meal."),
]

# ─── Tables — 10 tables, mixed capacities and zones ───────────────────────
TABLES = [
    {"table_number": 1,  "capacity": 2, "zone": "indoor",  "status": TableStatus.OCCUPIED},
    {"table_number": 2,  "capacity": 2, "zone": "indoor",  "status": TableStatus.AVAILABLE},
    {"table_number": 3,  "capacity": 2, "zone": "outdoor", "status": TableStatus.AVAILABLE},
    {"table_number": 4,  "capacity": 4, "zone": "indoor",  "status": TableStatus.OCCUPIED},
    {"table_number": 5,  "capacity": 4, "zone": "indoor",  "status": TableStatus.CLEANING},
    {"table_number": 6,  "capacity": 4, "zone": "outdoor", "status": TableStatus.AVAILABLE},
    {"table_number": 7,  "capacity": 6, "zone": "indoor",  "status": TableStatus.AVAILABLE},
    {"table_number": 8,  "capacity": 6, "zone": "outdoor", "status": TableStatus.OCCUPIED},
    {"table_number": 9,  "capacity": 8, "zone": "private", "status": TableStatus.AVAILABLE},
    {"table_number": 10, "capacity": 8, "zone": "private", "status": TableStatus.OUT_OF_SERVICE},
]

# ─── Menu — 15 items ──────────────────────────────────────────────────────
MENU_ITEMS = [
    # Starters
    {
        "name": "Burrata & Heirloom Tomato",
        "category": "Starters",
        "description": "Fresh burrata with heirloom tomatoes, basil oil, and aged balsamic glaze",
        "price": 580.0,
        "ingredients": "burrata, heirloom tomatoes, basil, olive oil, balsamic vinegar",
        "allergens": "dairy",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    {
        "name": "Crispy Calamari",
        "category": "Starters",
        "description": "Lightly battered calamari with saffron aioli and lemon",
        "price": 620.0,
        "ingredients": "squid, flour, saffron, garlic, lemon",
        "allergens": "gluten, seafood, eggs",
        "is_vegetarian": False,
        "is_vegan": False,
    },
    {
        "name": "Mushroom Crostini",
        "category": "Starters",
        "description": "Wild mushroom ragù on sourdough toast with truffle oil and fresh thyme",
        "price": 490.0,
        "ingredients": "wild mushrooms, sourdough bread, truffle oil, thyme, garlic",
        "allergens": "gluten",
        "is_vegetarian": True,
        "is_vegan": True,
    },
    # Mains
    {
        "name": "Saffron Risotto",
        "category": "Mains",
        "description": "Carnaroli rice with saffron, parmesan, and seasonal vegetables",
        "price": 780.0,
        "ingredients": "carnaroli rice, saffron, parmesan, butter, white wine, vegetables",
        "allergens": "dairy, alcohol",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    {
        "name": "Pan-Seared Atlantic Salmon",
        "category": "Mains",
        "description": "Atlantic salmon fillet with lemon butter sauce, capers, and seasonal greens",
        "price": 1150.0,
        "ingredients": "salmon, butter, lemon, capers, dill, mixed greens",
        "allergens": "fish, dairy",
        "is_vegetarian": False,
        "is_vegan": False,
    },
    {
        "name": "Lamb Rogan Josh",
        "category": "Mains",
        "description": "Slow-cooked Kashmiri lamb in aromatic spices, served with saffron basmati",
        "price": 1280.0,
        "ingredients": "lamb, Kashmiri chillies, yogurt, whole spices, basmati rice",
        "allergens": "dairy",
        "is_vegetarian": False,
        "is_vegan": False,
    },
    {
        "name": "Chargrilled Chicken",
        "category": "Mains",
        "description": "Herb-marinated chicken breast with roasted peppers and chimichurri",
        "price": 980.0,
        "ingredients": "chicken breast, herbs, peppers, garlic, parsley, olive oil",
        "allergens": "none",
        "is_vegetarian": False,
        "is_vegan": False,
    },
    {
        "name": "Wild Mushroom Linguine",
        "category": "Mains",
        "description": "Fresh egg pasta with wild mushrooms, garlic, white wine, and aged parmesan",
        "price": 820.0,
        "ingredients": "linguine, wild mushrooms, garlic, white wine, parmesan, cream",
        "allergens": "gluten, dairy, eggs, alcohol",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    {
        "name": "Paneer Tikka Masala",
        "category": "Mains",
        "description": "Tandoor-grilled paneer in a rich tomato and cashew masala with naan",
        "price": 720.0,
        "ingredients": "paneer, tomatoes, cashews, cream, spices, naan",
        "allergens": "dairy, gluten, tree nuts",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    {
        "name": "Grilled Tenderloin",
        "category": "Mains",
        "description": "250g Australian beef tenderloin, red wine jus, truffle butter, asparagus",
        "price": 1950.0,
        "ingredients": "beef, red wine, butter, truffle, asparagus, garlic",
        "allergens": "dairy, alcohol",
        "is_vegetarian": False,
        "is_vegan": False,
    },
    # Desserts
    {
        "name": "Dark Chocolate Fondant",
        "category": "Desserts",
        "description": "Warm Valrhona chocolate fondant with vanilla bean ice cream",
        "price": 420.0,
        "ingredients": "dark chocolate, butter, eggs, flour, vanilla ice cream",
        "allergens": "dairy, eggs, gluten",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    {
        "name": "Mango Panna Cotta",
        "category": "Desserts",
        "description": "Silky vanilla panna cotta with Alphonso mango coulis",
        "price": 380.0,
        "ingredients": "cream, gelatin, vanilla, Alphonso mango",
        "allergens": "dairy",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    # Drinks
    {
        "name": "Fresh Lime Soda",
        "category": "Beverages",
        "description": "House-made lime cordial with sparkling water, mint, and sugar",
        "price": 180.0,
        "ingredients": "lime juice, sparkling water, mint, sugar",
        "allergens": "none",
        "is_vegetarian": True,
        "is_vegan": True,
    },
    {
        "name": "Masala Chai",
        "category": "Beverages",
        "description": "Traditional spiced tea brewed with whole spices, milk, and jaggery",
        "price": 150.0,
        "ingredients": "black tea, milk, cardamom, ginger, cinnamon, cloves, jaggery",
        "allergens": "dairy",
        "is_vegetarian": True,
        "is_vegan": False,
    },
    {
        "name": "Watermelon Basil Cooler",
        "category": "Beverages",
        "description": "Fresh watermelon juice with basil, black pepper, and a hint of rose",
        "price": 220.0,
        "ingredients": "watermelon, basil, black pepper, rose water",
        "allergens": "none",
        "is_vegetarian": True,
        "is_vegan": True,
    },
]

# ─── Knowledge Documents — for RAG ────────────────────────────────────────
KNOWLEDGE_DOCS = [
    {
        "title": "About Aria Kitchen",
        "content": (
            "Aria Kitchen is a contemporary fine-dining restaurant in Koramangala, Bengaluru. "
            "We serve modern Indian and Mediterranean cuisine with seasonal, locally sourced ingredients. "
            "The restaurant seats up to 50 guests across indoor, outdoor terrace, and private dining zones. "
            "We are open Tuesday to Sunday for lunch and dinner, with extended hours on Friday and Saturday. "
            "On Mondays we are open for dinner only (7 PM to 11 PM). "
            "We are closed on Monday lunch. "
            "Aria Kitchen is a walk-in restaurant — we do not accept advance reservations."
        ),
    },
    {
        "title": "Opening Hours",
        "content": (
            "Aria Kitchen opening hours:\n"
            "Monday: 12:00 PM – 3:00 PM (lunch), 7:00 PM – 11:00 PM (dinner)\n"
            "Tuesday to Thursday: 12:00 PM – 11:00 PM\n"
            "Friday: 12:00 PM – 11:30 PM\n"
            "Saturday: 11:00 AM – 11:30 PM\n"
            "Sunday: 11:00 AM – 10:00 PM\n"
            "Last orders are taken 30 minutes before closing time."
        ),
    },
    {
        "title": "Walk-In Seating Policy",
        "content": (
            "Aria Kitchen is a walk-in only restaurant. We do not accept reservations of any kind. "
            "When you arrive, our AI receptionist will check the current table availability and seat you immediately "
            "if a suitable table is free. If all tables are occupied, we will give you an estimated wait time "
            "and add you to our waiting list. Tables are allocated on a first-come, first-served basis. "
            "We cannot hold tables without the full party present."
        ),
    },
    {
        "title": "Vegetarian and Vegan Menu Options",
        "content": (
            "Aria Kitchen offers a wide selection of vegetarian and vegan dishes. "
            "Vegetarian options include: Burrata & Heirloom Tomato, Mushroom Crostini, Saffron Risotto, "
            "Wild Mushroom Linguine, Paneer Tikka Masala, Dark Chocolate Fondant, and Mango Panna Cotta. "
            "Vegan options include: Mushroom Crostini, Fresh Lime Soda, and Watermelon Basil Cooler. "
            "Our kitchen can accommodate further dietary modifications — please inform your server. "
            "All dishes can be prepared without onion or garlic on request."
        ),
    },
    {
        "title": "Allergen Information",
        "content": (
            "Aria Kitchen takes allergens seriously. Common allergens present in our kitchen include: "
            "gluten (wheat), dairy, eggs, tree nuts (cashews), seafood, and alcohol (used in cooking). "
            "Gluten-free options include: Burrata & Heirloom Tomato, Pan-Seared Atlantic Salmon, "
            "Chargrilled Chicken, Fresh Lime Soda, and Watermelon Basil Cooler. "
            "Please inform your server of any allergies before ordering. "
            "While we take precautions, our kitchen is not a nut-free or allergen-free environment."
        ),
    },
    {
        "title": "Parking and Accessibility",
        "content": (
            "Parking: Aria Kitchen offers complimentary valet parking at the main entrance. "
            "Basement self-parking is available at ₹50 per hour. Street parking is available on Bougainvillea Lane. "
            "Accessibility: The restaurant is fully wheelchair accessible with ramp access at the entrance, "
            "wide aisles between tables, and an accessible restroom. "
            "If you have any specific accessibility requirements, please inform our team upon arrival."
        ),
    },
    {
        "title": "Pet Policy",
        "content": (
            "We love animals at Aria Kitchen. "
            "However, pets are not permitted inside the indoor dining room due to hygiene regulations. "
            "Leashed, well-behaved dogs are warmly welcome on our outdoor terrace seating area. "
            "Please bring a water bowl for your pet — we are happy to fill it for you. "
            "Other animals and exotic pets are not permitted on the premises."
        ),
    },
    {
        "title": "Payment Methods",
        "content": (
            "Aria Kitchen accepts the following payment methods: "
            "Credit cards (Visa, Mastercard, American Express), "
            "Debit cards (all major Indian banks), "
            "UPI payments (Google Pay, PhonePe, Paytm, BHIM), "
            "and Cash (Indian Rupees only). "
            "We do not accept foreign currency, cryptocurrency, or cheques. "
            "A GST of 5% is applicable on all food and beverages. "
            "A discretionary service charge of 10% may be added to the bill for groups of 8 or more."
        ),
    },
    {
        "title": "High Chairs and Children",
        "content": (
            "Children of all ages are welcome at Aria Kitchen. "
            "We have high chairs available for infants and toddlers at no charge. "
            "Please ask our receptionist or your server when you arrive. "
            "We have a small selection of mild, child-friendly dishes available on request. "
            "Baby food warmed on request — please speak to your server."
        ),
    },
    {
        "title": "Private Dining",
        "content": (
            "Aria Kitchen has a private dining room that can seat up to 8 guests. "
            "The private dining room is available for special occasions and group bookings. "
            "Availability is subject to current seating demand — please ask our receptionist when you arrive. "
            "We can arrange birthday cakes, special decorations, and customised menus with advance notice — "
            "please call us at +91-80-4567-8900 to arrange."
        ),
    },
    {
        "title": "Wi-Fi",
        "content": (
            "Complimentary Wi-Fi is available throughout Aria Kitchen for all guests. "
            "Network: AriaKitchen_Guest. "
            "Password: available from your server or receptionist. "
            "The connection is suitable for browsing and streaming."
        ),
    },
    {
        "title": "Outside Food and Dress Code",
        "content": (
            "Outside food and beverages are not permitted on the premises. "
            "Birthday cakes purchased externally may be brought in with prior arrangement — a plating charge applies. "
            "Dress code: Smart casual is recommended for the indoor dining room. "
            "Beachwear, flip-flops, and sports shorts are not appropriate. "
            "The outdoor terrace has a relaxed dress code."
        ),
    },
]


async def seed(session: AsyncSession) -> None:
    """Seed the database with Aria Kitchen data."""
    # Check if already seeded
    from sqlalchemy import select
    result = await session.execute(select(Restaurant))
    if result.scalars().first():
        print("Database already seeded — skipping.")
        return

    print("Seeding Aria Kitchen data...")

    # Restaurant
    restaurant = Restaurant(**RESTAURANT)
    session.add(restaurant)
    await session.flush()  # get the ID

    # Hours
    for h in HOURS:
        session.add(RestaurantHour(restaurant_id=restaurant.id, **h))

    # Policies
    for key, value in POLICIES:
        session.add(RestaurantPolicy(restaurant_id=restaurant.id, key=key, value=value))

    # Tables
    for t in TABLES:
        session.add(RestaurantTable(restaurant_id=restaurant.id, **t))

    # Menu items
    for m in MENU_ITEMS:
        session.add(MenuItem(restaurant_id=restaurant.id, **m))

    # Knowledge documents (embeddings added later by RAG service)
    for doc in KNOWLEDGE_DOCS:
        session.add(KnowledgeDocument(
            restaurant_id=restaurant.id,
            title=doc["title"],
            content=doc["content"],
            embedding=None,  # will be populated by rag_service.embed_all()
        ))

    await session.commit()
    print(f"[SUCCESS] Seeded: 1 restaurant, {len(HOURS)} hours, {len(POLICIES)} policies, "
          f"{len(TABLES)} tables, {len(MENU_ITEMS)} menu items, {len(KNOWLEDGE_DOCS)} knowledge docs")


async def run_seed() -> None:
    """Entry point for seeding."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(run_seed())
