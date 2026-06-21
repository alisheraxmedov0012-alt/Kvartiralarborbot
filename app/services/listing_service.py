from app.database.session import async_session
from app.database import queries

class ListingService:
    @staticmethod
    async def save_new_listing(tg_id: int, data: dict, photos: list):
        async with async_session() as session:
            user = await queries.get_or_create_user(session, tg_id, data.get('full_name', 'User'))
            listing = await queries.create_listing(session, user.id, data, photos)
            return listing

    @staticmethod
    async def delete_listing(listing_id: int):
        async with async_session() as session:
            listing = await queries.get_listing_by_id(session, listing_id)
            if listing:
                await session.delete(listing)
                await session.commit()
                return True
            return False
          
