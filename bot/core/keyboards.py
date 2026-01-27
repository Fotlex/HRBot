from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мои документы"), KeyboardButton(text="Квизы")],
        [KeyboardButton(text="О компании"), KeyboardButton(text="Помощь")],
    ],
    resize_keyboard=True
)

class DocumentCallback(CallbackData, prefix="doc"):
    document_id: int

def get_documents_keyboard(documents) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for doc in documents:
        builder.button(
            text=doc.title,
            callback_data=DocumentCallback(document_id=doc.id)
        )
    builder.adjust(1)
    return builder.as_markup()


class QuizCallback(CallbackData, prefix="quiz"):
    quiz_id: int

def get_quizzes_keyboard(quizzes, user_attempts) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    attempts_map = {attempt.quiz_id: attempt for attempt in user_attempts}

    for quiz in quizzes:
        attempt = attempts_map.get(quiz.id)
        if attempt:
            status = "✅ Пройден"
        else:
            status = "❌ Не пройден"
        
        builder.button(
            text=f"{quiz.title} - {status}",
            callback_data=QuizCallback(quiz_id=quiz.id)
        )
    builder.adjust(1)
    return builder.as_markup()


class AnswerCallback(CallbackData, prefix="ans"):
    answer_id: int

def get_answers_keyboard(answers) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for answer in answers:
        builder.button(
            text=answer.text,
            callback_data=AnswerCallback(answer_id=answer.id)
        )
    builder.adjust(1)
    return builder.as_markup()


class AboutCallback(CallbackData, prefix="about"):
    section_id: int

def get_about_keyboard(sections) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for section in sections:
        builder.button(
            text=section.title,
            callback_data=AboutCallback(section_id=section.id)
        )
    builder.adjust(1)
    return builder.as_markup()


def get_back_to_about_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад к списку", callback_data="back_to_about_list")
    return builder.as_markup()