from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, ARRAY, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


# ===================== ПОЛЬЗОВАТЕЛЬ =====================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))

    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    desc = Column(Text, nullable=True)
    specialization = Column(String, nullable=True)

    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=True)

    # S3 ID аватарки
    avatar_id = Column(String, nullable=True)

    rating = Column(Float, default=0.0)
    balance = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="client")  # "client" или "freelancer"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    received_reviews = relationship("Review", foreign_keys="Review.receiver_id", back_populates="receiver")
    written_reviews = relationship("Review", foreign_keys="Review.author_id", back_populates="author")
    portfolio_items = relationship("Portfolio", back_populates="user")
    kworks = relationship("Kwork", back_populates="user")
    skills = relationship("Skill", secondary="user_skills", back_populates="users")


# ===================== НАВЫКИ (MANY-TO-MANY) =====================
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", secondary="user_skills", back_populates="skills")


class UserSkill(Base):
    __tablename__ = "user_skills"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)


# ===================== ОТЗЫВЫ =====================
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    author = relationship("User", foreign_keys=[author_id], back_populates="written_reviews")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_reviews")


# ===================== ПОРТФОЛИО =====================
class Portfolio(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    photo_id = Column(String, nullable=True)  # S3 ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="portfolio_items")


# ===================== КВОРКИ (ЗАКАЗЫ) И ТЕГИ =====================
class Kwork(Base):
    __tablename__ = "kworks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    desc = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String, default="not_completed")  # not_completed, in_process, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Исполнитель
    client_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Клиент

    # Хранение списка фото (массив строк для S3 ID)
    photos = Column(ARRAY(String), nullable=True)

    user = relationship("User", back_populates="kworks")
    client = relationship("User", foreign_keys=[client_id])
    tags = relationship("Tag", secondary="kwork_tags", back_populates="kworks")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    kworks = relationship("Kwork", secondary="kwork_tags", back_populates="tags")


class KworkTag(Base):
    __tablename__ = "kwork_tags"
    kwork_id = Column(Integer, ForeignKey("kworks.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


# ===================== ЧАТЫ И СООБЩЕНИЯ =====================
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    initiator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kwork_id = Column(Integer, ForeignKey("kworks.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    initiator = relationship("User", foreign_keys=[initiator_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    kwork = relationship("Kwork")
    messages = relationship("Message", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User")