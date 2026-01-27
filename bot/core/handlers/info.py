from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from web.panel.models import AboutSection
from ..keyboards import get_about_keyboard, AboutCallback, get_back_to_about_keyboard

router = Router()

@router.message(F.text == "О компании")
async def handle_about(message: Message):
    sections = [s async for s in AboutSection.objects.all().order_by('order')]
    
    if not sections:
        await message.answer("Информация о компании пока не добавлена.")
        return

    await message.answer(
        "Выберите интересующий вас раздел:",
        reply_markup=get_about_keyboard(sections)
    )


@router.callback_query(AboutCallback.filter())
async def handle_about_section_press(query: CallbackQuery, callback_data: AboutCallback):
    section_id = callback_data.section_id
    try:
        section = await AboutSection.objects.aget(id=section_id)
        
        await query.message.edit_text(
            text=f"🏢 *{section.title}*\n\n{section.text}",
            parse_mode="Markdown",
            reply_markup=get_back_to_about_keyboard()
        )
    except AboutSection.DoesNotExist:
        await query.answer("Раздел был удален.", show_alert=True)
        await handle_back_to_list(query)


@router.callback_query(F.data == "back_to_about_list")
async def handle_back_to_list(query: CallbackQuery):
    sections = [s async for s in AboutSection.objects.all().order_by('order')]
    
    await query.message.edit_text(
        "Выберите интересующий вас раздел:",
        reply_markup=get_about_keyboard(sections)
    )