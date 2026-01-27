from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from web.panel.models import Document, User
from ..keyboards import DocumentCallback, get_documents_keyboard

router = Router()

@router.message(F.text == "Мои документы")
async def handle_my_documents(message: Message, user: User):
    if not user.department:
        await message.answer("Вам еще не назначено подразделение. Обратитесь к HR-менеджеру.")
        return

    documents = [doc async for doc in Document.objects.filter(department=user.department)]

    if not documents:
        await message.answer("Для вашего подразделения пока нет документов.")
        return

    await message.answer(
        "Вот список доступных вам документов:",
        reply_markup=get_documents_keyboard(documents)
    )

@router.callback_query(DocumentCallback.filter())
async def handle_document_press(query: CallbackQuery, callback_data: DocumentCallback, bot: Bot):
    document_id = callback_data.document_id
    try:
        document = await Document.objects.aget(id=document_id)
        
        file_to_send = FSInputFile(document.file.path)
        
        await bot.send_document(
            chat_id=query.from_user.id,
            document=file_to_send,
            caption=document.description
        )
        await query.answer() 
    except Document.DoesNotExist:
        await query.answer("Ошибка: документ был удален.", show_alert=True)
    except FileNotFoundError:
        await query.answer("Ошибка: файл документа не найден на сервере.", show_alert=True)