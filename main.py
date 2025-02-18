import asyncio
from aiogram import Bot, Dispatcher
from app.core.config import settings
from app.bot.handlers import user_handlers, user_callbacks, admin_panel
from app.database.connection import init_db
from aiogram.fsm.storage.memory import MemoryStorage


def register_handlers(dp: Dispatcher):
    # Сначала регистрируем общие обработчики
    dp.include_router(user_handlers.router)
    # Затем специфические обработчики
    dp.include_router(admin_panel.router)
    # В конце обработчики callback'ов
    dp.include_router(user_callbacks.router)

async def main():
    # Инициализация базы данных
    init_db()
    
    # Инициализация бота и диспетчера с хранилищем состояний
    bot = Bot(token=settings.TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация обработчиков
    register_handlers(dp)

    try:
        # Запуск поллинга
        await dp.start_polling(bot, 
            polling_timeout=30,  # Таймаут между запросами
            allowed_updates=["message", "callback_query"],  # Типы обновлений, которые мы хотим получать
        )
    finally:
        # Гарантированное закрытие бота после остановки поллинга
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())