"""Idempotent database seed for local development and demos."""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Allow `python scripts/seed_database.py` from the backend directory.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.enums import HcpStatus, MaterialType, UserRole
from app.models.hcp import Hcp
from app.models.interaction_type import InteractionType
from app.models.material import Material
from app.models.product import Product
from app.models.sample import Sample
from app.models.topic import Topic
from app.models.user import User
from app.utils.environment import load_environment

load_environment()

DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_PRODUCT_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")

INTERACTION_TYPES = [
    ("Meeting", "In-person or scheduled meeting with an HCP"),
    ("Call", "Phone or virtual call interaction"),
    ("Face to Face", "Direct face-to-face engagement"),
    ("Virtual Meeting", "Video or remote meeting"),
    ("Conference", "Conference or congress interaction"),
]

TOPICS = [
    ("CardioMax efficacy", "Clinical", "Efficacy data for CardioMax"),
    ("CardioMax safety profile", "Clinical", "Safety and tolerability discussion"),
    ("Dosing guidance", "Medical", "Dosing recommendations"),
    ("Patient adherence", "Medical", "Adherence support strategies"),
]

MATERIALS = [
    ("Product brochure", MaterialType.BROCHURE, "CardioMax product brochure"),
    ("Clinical study summary", MaterialType.CLINICAL_STUDY, "Pivotal trial summary"),
    ("Product leaflet", MaterialType.PRODUCT_LEAFLET, "HCP-facing product leaflet"),
]

SAMPLES = [
    ("CardioMax sample pack", "LOT-CM-2026-01", 250),
    ("CardioMax starter kit", "LOT-CM-2026-02", 120),
]

HCPS = [
    {
        "name": "Dr Sharma",
        "specialization": "Cardiology",
        "hospital": "Apollo Hospital",
        "city": "Mumbai",
        "state": "Maharashtra",
        "email": "dr.sharma@apollo.example.com",
        "phone": "+91-98765-43210",
    },
    {
        "name": "Dr Gupta",
        "specialization": "Cardiology",
        "hospital": "Apollo Hospital",
        "city": "Delhi",
        "state": "Delhi",
        "email": "dr.gupta@apollo.example.com",
        "phone": "+91-98765-43211",
    },
    {
        "name": "Dr John",
        "specialization": "Internal Medicine",
        "hospital": "City Medical Center",
        "city": "Bangalore",
        "state": "Karnataka",
        "email": "dr.john@citymed.example.com",
        "phone": "+91-98765-43212",
    },
    {
        "name": "Dr Jane Smith",
        "specialization": "Cardiology",
        "hospital": "Metro Heart Institute",
        "city": "Boston",
        "state": "MA",
        "email": "jane.smith@metroheart.example.com",
        "phone": "+1-555-0100",
    },
]


async def seed() -> None:
    """Populate reference data required for AI chat and interaction save flows."""
    async with async_session_factory() as session:
        existing_user = await session.get(User, DEMO_USER_ID)
        if existing_user is None:
            session.add(
                User(
                    id=DEMO_USER_ID,
                    first_name="Alex",
                    last_name="Representative",
                    email="alex.rep@healthcare-crm.example.com",
                    password_hash="dev-only-not-for-production",
                    role=UserRole.MEDICAL_REPRESENTATIVE,
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                ),
            )

        product = await session.get(Product, DEMO_PRODUCT_ID)
        if product is None:
            session.add(
                Product(
                    id=DEMO_PRODUCT_ID,
                    product_name="CardioMax",
                    brand="CardioMax",
                    category="Cardiology",
                    description="Cardiovascular therapy for HCP engagement demos",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                ),
            )

        await session.flush()

        for name, description in INTERACTION_TYPES:
            result = await session.execute(
                select(InteractionType).where(InteractionType.name == name),
            )
            if result.scalar_one_or_none() is None:
                session.add(
                    InteractionType(
                        name=name,
                        description=description,
                        is_active=True,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    ),
                )

        for name, category, description in TOPICS:
            result = await session.execute(select(Topic).where(Topic.name == name))
            if result.scalar_one_or_none() is None:
                session.add(
                    Topic(
                        name=name,
                        category=category,
                        description=description,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    ),
                )

        for name, material_type, description in MATERIALS:
            result = await session.execute(select(Material).where(Material.name == name))
            if result.scalar_one_or_none() is None:
                session.add(
                    Material(
                        name=name,
                        material_type=material_type,
                        description=description,
                        product_id=DEMO_PRODUCT_ID,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    ),
                )

        for name, lot_number, quantity in SAMPLES:
            result = await session.execute(select(Sample).where(Sample.name == name))
            if result.scalar_one_or_none() is None:
                session.add(
                    Sample(
                        name=name,
                        lot_number=lot_number,
                        quantity_available=quantity,
                        product_id=DEMO_PRODUCT_ID,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    ),
                )

        for hcp_data in HCPS:
            result = await session.execute(select(Hcp).where(Hcp.name == hcp_data["name"]))
            if result.scalar_one_or_none() is None:
                session.add(
                    Hcp(
                        status=HcpStatus.ACTIVE,
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                        **hcp_data,
                    ),
                )

        await session.commit()
        print("Database seeded successfully.")
        print(f"Demo user ID: {DEMO_USER_ID}")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
