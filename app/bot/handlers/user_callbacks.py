from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from app.services.subscription import SubscriptionService
from app.bot.keyboards.user_keyboard import get_start_keyboard, get_configuration_keyboard, get_admin_keyboard
from app.database.repositories.server_repo import ServerRepository
from app.database.connection import get_db
from app.core.config import settings

router = Router()

@router.callback_query(F.data == "start_callback")
async def start_button(callback: CallbackQuery):


    service = SubscriptionService()
    status = await service.get_subscription_status(callback.from_user.id)
    user = await service.get_user_by_telegram_id(callback.from_user.id)

    if callback.from_user.id in settings.ADMIN_IDS:
        text, keyboard = get_admin_keyboard(status,user)
    else:
        text, keyboard = get_start_keyboard(status,user)

    await callback.answer()
    await callback.message.answer_photo(
        photo=FSInputFile("app/images/TG_message_LC.png"),
        caption=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    

@router.callback_query(F.data == "extend_subscription")
async def extend_subscription_pay(callback: CallbackQuery):
    try:
        service = SubscriptionService()
        user = await service.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("Сначала зарегистрируйтесь с помощью /start.")
            return

        payment_url = "https://example.com/payment_link"
        await callback.answer()
        await callback.message.answer(
            f"<b>Для оплаты, пожалуйста, воспользуйтесь этой ссылкой:</b>\n\n<a href='{payment_url}'>{payment_url}</a>\n\nЕсли у вас возникнут вопросы, мы готовы помочь!", 
            parse_mode="HTML"
        )
        text = await service.extend_subscription(callback.from_user.id, 1)
        keyboard = get_configuration_keyboard()
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    except Exception as e:
        print(f"Error in extend_subscription_pay: {e}")
        await callback.message.answer(
            "Произошла ошибка при обработке запроса. Пожалуйста, обратитесь в тех. поддержку.",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "pay_subscription")
async def pay_subscription(callback: CallbackQuery):
    try:
        service = SubscriptionService()
        user = await service.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("Сначала зарегистрируйтесь с помощью /start.")
            return

        # Проверяем наличие свободного сервера через сервисный слой
        server = await service.check_free_server()
        if not server:
            await callback.answer()
            await callback.message.edit_text(
                "К сожалению, сейчас нет свободных серверов 😔\n\nМы работаем над их добавлением. Попробуйте позже.",
                parse_mode="HTML"
            )
            return

        payment_url = "https://example.com/payment_link"
        await callback.answer()
        await callback.message.edit_text(
            f"<b>Для оплаты, пожалуйста, воспользуйтесь этой ссылкой:</b>\n\n<a href='{payment_url}'>{payment_url}</a>\n\nЕсли у вас возникнут вопросы, мы готовы помочь!", 
            parse_mode="HTML"
        )
        text = await service.pay_subscription(callback.from_user.id, 1)
        keyboard = get_configuration_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    

    except Exception as e:
        print(f"Error in pay_subscription: {e}")
        await callback.message.edit_text(
            "Произошла ошибка при обработке запроса. Пожалуйста, обратитесь в тех. поддержку.",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "get_configuration")
async def get_configuration(callback: CallbackQuery):
    service = SubscriptionService()
    user = await service.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "⚠️ У вас нет активной подписки!\n\n"
            "Для получения конфигурации необходимо оплатить подписку.",
            reply_markup=get_configuration_keyboard(),
            parse_mode="HTML"
        )
        return
    text = await service.get_configuration(callback.from_user.id)
    keyboard = get_configuration_keyboard()
    await callback.message.edit_caption(
        caption=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
    

def get_start_message(user, subscription_end=None, balance=0):
    status = "Активна 🟢" if user.status == "active" else "Неактивна 🔴"
    sub_end = subscription_end.strftime("%d.%m.%Y") if subscription_end else "Нет активной подписки"
    
    return (
        f"👋 Привет, {user.username}! 🚀\n\n"
        f"Добро пожаловать в личный кабинет! Здесь вы найдёте информацию о своём аккаунте, подписке и использовании трафика.\n\n"
        f"📌 Данные аккаунта:\n"
        f"🔹 Ваш статус подписки: {status}\n"
        f"🔹 Действует до: {sub_end} 📅\n\n"
        f"🪙 Баланс: {balance} рублей\n\n"
        f"🔑 Доступ к сервису:\n"
        f"Чтобы подключиться, просто перейдите по ссылке:\n\n"
        f"➡️ [Ваша ссылка]\n\n"
        f"👆 Нажмите, чтобы открыть, или загляните в раздел 📖 «Помощь в подключении» — там есть инструкции по настройке.\n\n"
        f"ℹ️ Дополнительная информация\n"
        f"Все подробности об установке и доступных приложениях вы найдёте в разделе 📖 «Помощь в подключении»."
    )
    
