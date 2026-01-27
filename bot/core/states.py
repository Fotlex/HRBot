from aiogram.fsm.state import StatesGroup, State

class QuizState(StatesGroup):
    in_quiz = State()