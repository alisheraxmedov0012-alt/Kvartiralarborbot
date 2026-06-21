from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database.models import User, Listing, Photo, ListingStatus

async def get_or_create_user(session: AsyncSession, tg_id: int, full_name: str, username: str = None, referrer_id: int = None):
    stmt = select(User).where(User.telegram_id == tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=tg_id, full_name=full_name, username=username, referrer_id=referrer_id)
        session.add(user)
        await session.commit()
    return user

async def create_listing(session: AsyncSession, user_id: int, data: dict, photos: list) -> Listing:
    listing = Listing(
        user_id=user_id,
        region=data['region'],
        district=data['district'],
        address=data['address'],
        rooms=int(data['rooms']),
        floor=data['floor'],
        price=data['price'],
        description=data['description'],
        is_vip=data.get('is_vip', False)
    )
    session.add(listing)
    await session.flush()
    
    for photo_id in photos:
        p = Photo(listing_id=listing.id, telegram_file_id=photo_id)
        session.add(p)
    
    await session.commit()
    return listing

async def get_user_listings(session: AsyncSession, tg_id: int):
    stmt = select(Listing).join(User).where(User.telegram_id == tg_id).orm_relationship_options()
    # E'lonlarni rasmlari bilan olish
    stmt = select(Listing).join(User).where(User.telegram_id == tg_id)
    res = await session.execute(stmt)
    return res.scalars().all()

async def get_listing_by_id(session: AsyncSession, listing_id: int):
    stmt = select(Listing).where(Listing.id == listing_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

async def get_photos_by_listing(session: AsyncSession, listing_id: int):
    stmt = select(Photo).where(Photo.listing_id == listing_id)
    res = await session.execute(stmt)
    return res.scalars().all()

async def update_listing_status(session: AsyncSession, listing_id: int, status: ListingStatus):
    stmt = select(Listing).where(Listing.id == listing_id)
    res = await session.execute(stmt)
    listing = res.scalar_one_or_none()
    if listing:
        listing.status = status
        await session.commit()
    return listing

async def get_stats(session: AsyncSession):
    u_count = await session.execute(select(func.count(User.id)))
    l_count = await session.execute(select(func.count(Listing.id)))
    p_count = await session.execute(select(func.count(Listing.id)).where(Listing.status == ListingStatus.PENDING))
    return {
        "users": u_count.scalar(),
        "listings": l_count.scalar(),
        "pending": p_count.scalar()
    }

async def get_pending_listings(session: AsyncSession):
    stmt = select(Listing).where(Listing.status == ListingStatus.PENDING)
    res = await session.execute(stmt)
    return res.scalars().all()

async def search_listings(session: AsyncSession, rooms: int = None, max_price: int = None):
    stmt = select(Listing).where(Listing.status == ListingStatus.APPROVED)
    if rooms:
        stmt = stmt.where(Listing.rooms == rooms)
    res = await session.execute(stmt)
    return res.scalars().all()
  
