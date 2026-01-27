from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from web.panel.models import User, Quiz, QuizAttempt, Question, Answer, UserAnswer
from ..keyboards import get_quizzes_keyboard, QuizCallback, get_answers_keyboard, AnswerCallback
from ..states import QuizState

router = Router()


@router.message(F.text == "Квизы")
async def handle_my_quizzes(message: Message, user: User):
    if not user.department:
        await message.answer("Вам еще не назначено подразделение. Обратитесь к HR-менеджеру.")
        return

    quizzes = [quiz async for quiz in Quiz.objects.filter(department=user.department)]
    if not quizzes:
        await message.answer("Для вашего подразделения пока нет тестов.")
        return

    user_attempts = [attempt async for attempt in QuizAttempt.objects.filter(user=user)]

    await message.answer(
        "Вот список доступных вам тестов:",
        reply_markup=get_quizzes_keyboard(quizzes, user_attempts)
    )


@router.callback_query(QuizCallback.filter())
async def handle_start_quiz(query: CallbackQuery, callback_data: QuizCallback, state: FSMContext, user: User):
    quiz_id = callback_data.quiz_id
    
    if await QuizAttempt.objects.filter(user=user, quiz_id=quiz_id).aexists():
        await query.answer("Вы уже проходили этот тест.", show_alert=True)
        return

    questions = [q async for q in Question.objects.filter(quiz_id=quiz_id).order_by('id')]
    if not questions:
        await query.answer("В этом тесте пока нет вопросов.", show_alert=True)
        return

    question_ids = [q.id for q in questions]

    await state.set_state(QuizState.in_quiz)
    await state.update_data(
        quiz_id=quiz_id,
        question_ids=question_ids,
        current_question_index=0,
        score=0,
        user_answers=[]
    )
    
    await query.answer()
    await send_question(query.message, state)


async def send_question(message: Message, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("question_ids", [])
    current_index = data.get("current_question_index", 0)

    if current_index >= len(question_ids):
        await finish_quiz(message, state)
        return

    question_id = question_ids[current_index]
    question = await Question.objects.aget(id=question_id)
    answers = [ans async for ans in Answer.objects.filter(question_id=question_id)]
    
    await message.answer(
        f"Вопрос {current_index + 1}/{len(question_ids)}:\n\n{question.text}",
        reply_markup=get_answers_keyboard(answers)
    )


@router.callback_query(AnswerCallback.filter(), QuizState.in_quiz)
async def handle_answer(query: CallbackQuery, callback_data: AnswerCallback, state: FSMContext):
    answer_id = callback_data.answer_id
    answer = await Answer.objects.select_related('question').aget(id=answer_id)
    
    data = await state.get_data()
    score = data.get("score", 0)
    user_answers = data.get("user_answers", [])

    user_answers.append({
        'question_id': answer.question.id,
        'answer_id': answer.id
    })

    if answer.is_correct:
        score += 1
        
    current_index = data.get("current_question_index", 0)
    await state.update_data(
        score=score,
        current_question_index=current_index + 1,
        user_answers=user_answers
    )

    await query.message.delete()
    await query.answer()
    
    await send_question(query.message, state)


async def finish_quiz(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.chat.id
    
    attempt = await QuizAttempt.objects.acreate(
        user_id=user_id,
        quiz_id=data.get("quiz_id"),
        score=data.get("score", 0)
    )

    user_answers_to_create = [
        UserAnswer(
            attempt=attempt,
            question_id=ans['question_id'],
            answer_id=ans['answer_id']
        )
        for ans in data.get("user_answers", [])
    ]
    await UserAnswer.objects.abulk_create(user_answers_to_create)

    total_questions = len(data.get("question_ids", []))
    score = data.get("score", 0)

    await message.answer(
        f"Тест завершён!\n\nВаш результат: {score} из {total_questions} правильных ответов."
    )
    
    await state.clear()