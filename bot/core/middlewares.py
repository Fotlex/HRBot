from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from web.panel.models import User

class UserMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        from_user = event.from_user

        try:
            user = await User.objects.select_related("department").aget(id=from_user.id)
            created = False
        except User.DoesNotExist:
            user, created = await User.objects.aget_or_create(id=from_user.id)

        if created:
            user.username = from_user.username
            user.first_name = from_user.first_name
            user.last_name = from_user.last_name
            await user.asave()
            await event.answer("Здравствуйте! Ваша заявка на доступ принята и ожидает подтверждения от HR-менеджера.")
            return
        
        if not user.is_active:
            await event.answer("Ваш доступ все еще ожидает подтверждения. Пожалуйста, ожидайте.",
                               show_alert=isinstance(event, CallbackQuery))
            return

        data['user'] = user
        return await handler(event, data)