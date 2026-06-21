import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app import models
from app.schemas import UserCreate, KworkCreate
from app.hashing import get_password_hash, generate_salt


async def create_user(db: AsyncSession, user_data: UserCreate):
    salt = generate_salt()
    hashed_password = get_password_hash(user_data.password, salt)

    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        description=user_data.description,
        specialization=user_data.specialization,
        password_hash=hashed_password,
        password_salt=salt,
        uuid=str(uuid.uuid4()),
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def create_kwork(db: AsyncSession, kwork_data: KworkCreate, user_id: int):
    photo_ids_str = ",".join(kwork_data.photo_ids) if kwork_data.photo_ids else None

    db_kwork = models.Kwork(
        title=kwork_data.title,
        description=kwork_data.description,
        price=kwork_data.price,
        photo_ids=photo_ids_str,
        user_id=user_id,
        status=models.KworkStatus.NOT_COMPLETED
    )
    db.add(db_kwork)
    await db.flush()

    for tag_id in kwork_data.tag_ids:
        tag = await db.get(models.Tag, tag_id)
        if tag:
            db.add(models.kwork_tag(kwork_id=db_kwork.id, tag_id=tag.id))

    await db.commit()
    await db.refresh(db_kwork)
    return db_kwork

async def get_kworks(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.Kwork)
        .options(selectinload(models.Kwork.tags))
        .offset(skip)
        .limit(limit)
        .order_by(models.Kwork.created_at.desc())
    )
    return result.scalars().all()

async def get_kwork_by_id(db: AsyncSession, kwork_id: int):
    result = await db.execute(
        select(models.Kwork)
        .options(selectinload(models.Kwork.tags))
        .where(models.Kwork.id == kwork_id)
    )
    return result.scalar_one_or_none()


async def update_kwork_status(
        db: AsyncSession,
        kwork_id: int,
        status: models.KworkStatus,
        client_id: int | None = None
):
    kwork = await get_kwork_by_id(db, kwork_id)
    if not kwork:
        return None

    kwork.status = status
    if client_id is not None:
        kwork.client_id = client_id
        await create_chat(db, kwork.user_id, client_id, kwork_id)

    await db.commit()
    await db.refresh(kwork)
    return kwork

async def create_chat(
        db: AsyncSession,
        initiator_id: int,
        receiver_id: int,
        kwork_id: int | None = None
):
    existing = await db.execute(
        select(models.Chat).where(models.Chat.kwork_id == kwork_id)
    )
    if existing.scalar_one_or_none():
        return existing.scalar_one_or_none()

    chat = models.Chat(
        initiator_id=initiator_id,
        receiver_id=receiver_id,
        kwork_id=kwork_id
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat