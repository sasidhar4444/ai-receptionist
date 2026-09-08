"""SQLAlchemy ORM models for the AI Restaurant Receptionist."""
from datetime import datetime, time
from enum import Enum as PyEnum
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer,
    String, Text, Time, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────
class TableStatus(str, PyEnum):
    """Live table states. NO RESERVED STATE — walk-in only."""
    AVAILABLE     = "AVAILABLE"
    OCCUPIED      = "OCCUPIED"
    CLEANING      = "CLEANING"
    READY         = "READY"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class DayOfWeek(str, PyEnum):
    MONDAY    = "monday"
    TUESDAY   = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY  = "thursday"
    FRIDAY    = "friday"
    SATURDAY  = "saturday"
    SUNDAY    = "sunday"


# ─── Restaurant ───────────────────────────────────────────────────────────
class Restaurant(Base):
    __tablename__ = "restaurants"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:        Mapped[str]           = mapped_column(String(200), nullable=False)
    address:     Mapped[Optional[str]] = mapped_column(Text)
    phone:       Mapped[Optional[str]] = mapped_column(String(50))
    timezone:    Mapped[str]           = mapped_column(String(100), default="Asia/Kolkata")
    description: Mapped[Optional[str]] = mapped_column(Text)

    hours:      Mapped[list["RestaurantHour"]]   = relationship(back_populates="restaurant")
    policies:   Mapped[list["RestaurantPolicy"]] = relationship(back_populates="restaurant")
    menu_items: Mapped[list["MenuItem"]]         = relationship(back_populates="restaurant")
    tables:     Mapped[list["RestaurantTable"]]  = relationship(back_populates="restaurant")
    knowledge:  Mapped[list["KnowledgeDocument"]] = relationship(back_populates="restaurant")


class RestaurantHour(Base):
    __tablename__ = "restaurant_hours"

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int]      = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    day_of_week:   Mapped[str]      = mapped_column(String(20), nullable=False)
    open_at:       Mapped[Optional[time]]  = mapped_column(Time)
    close_at:      Mapped[Optional[time]]  = mapped_column(Time)
    is_closed:     Mapped[bool]     = mapped_column(Boolean, default=False)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="hours")


class RestaurantPolicy(Base):
    __tablename__ = "restaurant_policies"

    id:            Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    key:           Mapped[str] = mapped_column(String(100), nullable=False)
    value:         Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (UniqueConstraint("restaurant_id", "key"),)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="policies")


# ─── Menu ─────────────────────────────────────────────────────────────────
class MenuItem(Base):
    __tablename__ = "menu_items"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int]           = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name:          Mapped[str]           = mapped_column(String(200), nullable=False)
    category:      Mapped[str]           = mapped_column(String(100), nullable=False)
    description:   Mapped[Optional[str]] = mapped_column(Text)
    price:         Mapped[float]         = mapped_column(Float, nullable=False)
    ingredients:   Mapped[Optional[str]] = mapped_column(Text)
    allergens:     Mapped[Optional[str]] = mapped_column(Text)
    is_vegetarian: Mapped[bool]          = mapped_column(Boolean, default=False)
    is_vegan:      Mapped[bool]          = mapped_column(Boolean, default=False)
    is_available:  Mapped[bool]          = mapped_column(Boolean, default=True)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_items")


# ─── Tables ───────────────────────────────────────────────────────────────
class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id:            Mapped[int]         = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int]         = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    table_number:  Mapped[int]         = mapped_column(Integer, nullable=False)
    capacity:      Mapped[int]         = mapped_column(Integer, nullable=False)
    zone:          Mapped[str]         = mapped_column(String(100), default="indoor")
    status:        Mapped[TableStatus] = mapped_column(
        String(20), default=TableStatus.AVAILABLE, nullable=False
    )
    updated_at:    Mapped[datetime]    = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="tables")

    __table_args__ = (UniqueConstraint("restaurant_id", "table_number"),)


# ─── Knowledge / RAG ──────────────────────────────────────────────────────
class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int]           = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    title:         Mapped[str]           = mapped_column(String(300), nullable=False)
    content:       Mapped[str]           = mapped_column(Text, nullable=False)
    # 1536 dims = text-embedding-3-small
    embedding:     Mapped[Optional[list[float]]] = mapped_column(Vector(1536))
    doc_metadata:  Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    created_at:    Mapped[datetime]      = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="knowledge")


# ─── Conversation Sessions ────────────────────────────────────────────────
class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    session_id:    Mapped[str]           = mapped_column(String(100), unique=True, nullable=False)
    restaurant_id: Mapped[int]           = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    state:         Mapped[str]           = mapped_column(String(50), default="idle")
    created_at:    Mapped[datetime]      = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at:    Mapped[datetime]      = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
