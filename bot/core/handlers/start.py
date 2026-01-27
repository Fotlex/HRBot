from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from ..keyboards import main_menu_keyboard
from web.panel.models import User

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message, user: User):
    await message.answer(
        f"Здравствуйте, {user.first_name}! Чем могу помочь?",
        reply_markup=main_menu_keyboard
    )