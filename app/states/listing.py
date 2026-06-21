from aiogram.fsm.state import State, StatesGroup

class ListingState(StatesGroup):
    region = State()
    district = State()
    address = State()
    rooms = State()
    floor = State()
    price = State()
    phone = State()
    description = State()
    photos = State()
    preview = State()
    edit_field = State()
  
