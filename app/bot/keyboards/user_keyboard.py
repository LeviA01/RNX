from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.vpn import VPNService

def get_start_keyboard(status, user):

    if status["active"]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продлить подписку", callback_data="extend_subscription")],
            [InlineKeyboardButton(text="Запросить конфигурацию", callback_data="get_configuration")]
        ])
        status = "Активна 🟢" if user.status == "active" else "Неактивна 🔴"
        text = (
            f"👋 <b>Привет, {user.username}!</b> 🚀\n\n"
            f"Добро пожаловать в личный кабинет! Здесь вы найдёте информацию о своём аккаунте, подписке и использовании трафика.\n\n"
            f"📌 <b>Данные аккаунта:</b>\n"
            f"🔹 Ваш статус подписки: <b>{status}</b>\n"
            f"🔹 Действует до: <b>{user.subscription_end} 📅</b>\n\n"
            f"🪙 Баланс: {0} рублей\n\n"
            f"🔑 Доступ к сервису:\n"
            f"Чтобы подключиться, просто перейдите по ссылке:\n\n"
            f"➡️ https://ronix-red.ru/{user.id}\n\n"
            f"👆 Нажмите, чтобы открыть, или загляните в раздел 📖 «Помощь в подключении» — там есть инструкции по настройке.\n\n"
        )
    else:

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить подписку", callback_data="pay_subscription")]
        ])
        text = (
            "<b>Подписка не активна</b> 😔\n\n"
            "Вы можете оформить или продлить её, чтобы вернуться к использованию сервиса! "
            "Мы всегда готовы помочь!"
        )

    return text, keyboard

def get_configuration_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад в меню:", callback_data="start_callback")]
    ])
    return keyboard

def get_admin_keyboard(status, user):
    if status["active"]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продлить подписку", callback_data="extend_subscription")],
            [InlineKeyboardButton(text="Запросить конфигурацию", callback_data="get_configuration")],
            [InlineKeyboardButton(text="Информация о пользователе", callback_data="userinfo")],
            [InlineKeyboardButton(text="Продлить подписку пользователя", callback_data="extend_user")],
            [InlineKeyboardButton(text="Заблокировать пользователя", callback_data="block_user")]
        ])
        status = "Активна 🟢" if user.status == "active" else "Неактивна 🔴"
        text = (
            f"👋 <b>Привет, {user.username}!</b> 🚀\n\n"
            f"Добро пожаловать в личный кабинет! Здесь вы найдёте информацию о своём аккаунте, подписке и использовании трафика.\n\n"
            f"📌 <b>Данные аккаунта:</b>\n"
            f"🔹 Ваш статус подписки: <b>{status}</b>\n"
            f"🔹 Действует до: <b>{user.subscription_end} 📅</b>\n\n"
            f"🪙 Баланс: {0} рублей\n\n"
            f"🔑 Доступ к сервису:\n"
            f"Чтобы подключиться, просто перейдите по ссылке:\n\n"
            f"➡️ https://ronix-red.ru/{user.id}\n\n"
            f"👆 Нажмите, чтобы открыть, или загляните в раздел 📖 «Помощь в подключении» — там есть инструкции по настройке.\n\n"
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить подписку", callback_data="pay_subscription")]
        ])
        text = (
            "<b>Подписка не активна</b> 😔\n\n"
            "Вы можете оформить или продлить её, чтобы вернуться к использованию сервиса! "
            "Мы всегда готовы помочь!"
        )
    return text, keyboard

def get_cancel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_action")]
    ])
    return keyboard




