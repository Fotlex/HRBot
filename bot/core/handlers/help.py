from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from web.panel.models import HelpButton, HelpPart
from ..keyboards import get_help_buttons_keyboard

router = Router()


@router.message(F.text == 'Помощь')
async def help_f(message: Message):
    buttons = [button async for button in HelpButton.objects.filter(is_active=True)]
    help_text = ''
    
    try:
        help_model = await HelpPart.objects.aget(id=1)
        help_text = help_model.text_on_message
    except Exception as e:
        help_text = 'Раздел "Помощь"'
        
    await message.answer(
        text=help_text,
        reply_markup=get_help_buttons_keyboard(buttons=buttons)
    )