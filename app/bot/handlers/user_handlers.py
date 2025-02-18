from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from app.services.subscription import SubscriptionService
from app.bot.keyboards.user_keyboard import get_start_keyboard, get_admin_keyboard
from app.core.config import settings

router = Router()


@router.message(F.text == "/start")
async def start_command(message: Message):

    service = SubscriptionService()
    user = await service.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        # Если пользователя нет, добавляем его
        await service.add_user(message.from_user.id, message.from_user.username)
    
    
    # Получаем статус подписки
    status = await service.get_subscription_status(message.from_user.id)
    if message.from_user.id in settings.ADMIN_IDS:
        text, keyboard = get_admin_keyboard(status, user)
    else:
        text, keyboard = get_start_keyboard(status, user)
    
    await message.answer_photo(
        photo=FSInputFile("app/images/TG_message_LC.png"),
        caption=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
