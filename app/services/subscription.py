import asyncio
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.server_repo import ServerRepository
from app.database.connection import get_db
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.services.vpn import VPNService
from aiogram.utils.markdown import hlink

class SubscriptionService:
    def __init__(self):
        self.db = next(get_db())
        self.user_repo = UserRepository(self.db)
        self.server_repo = ServerRepository(self.db)


    async def get_subscription_status(self, telegram_id: int) -> dict:
        user = self.user_repo.get_user(telegram_id)
        if not user or not user.subscription_end:
            return {
                "active": False,
                "expires": None
            }
        
        current_datetime = datetime.utcnow()
        return {
            "active": user.subscription_end > current_datetime,
            "expires": user.subscription_end
        }
    
    async def get_user_by_telegram_id(self, telegram_id: int):
        user = self.user_repo.get_user(telegram_id)
        return user

    async def extend_subscription(self, telegram_id: int, months: int):
        user = self.user_repo.get_user(telegram_id)

        if not user:
             return "Произошла ошибка при продлении подписки. Обратитесь в тех. поддержку."
        
        current_expiration = user.subscription_end
        new_expiration = current_expiration + relativedelta(months=months)
        self.user_repo.update_subscription(telegram_id, new_expiration)
        await asyncio.to_thread(VPNService.syns_user, user)
        text = f"<b>Подписка успешно продлена!</b> 🎉\n\nТеперь она активна до - {new_expiration.strftime('%d-%m-%Y')}.\n\nБлагодарим, что остаетесь с нами! ❤️"
        return text
    
    async def pay_subscription(self, telegram_id: int, months: int):
        user = self.user_repo.get_user(telegram_id)
        if not user:
            return "Произошла ошибка при оплате подписки. Обратитесь в тех. поддержку."
        
        current_expiration = user.subscription_end if user.subscription_end else datetime.utcnow()
        new_expiration = datetime.combine(current_expiration, datetime.min.time()) + relativedelta(months=months)
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "tgId": user.telegram_id,
            "subscription_end": new_expiration.strftime("%Y-%m-%d")
        }
        
        status, server_id = VPNService.add_vpn_user(user_data)
        
        if status:
            user.subscription_end = new_expiration
            user.server_id = server_id
            user.status = 'active'
            self.db.commit()
            
            # Обновляем количество пользователей на сервере
            self.server_repo.update_server_users(server_id)
            
            await asyncio.to_thread(VPNService.syns_user, user)
            url = f"https://ronix-red.ru/{user.id}"
            
            return f"<b>Ваша конфигурация успешно создана! 🎉</b>\n\n🔗 Нажми на ссылку, чтобы импортировать конфиг в Hiddify:\n\n<a href='{url}'>Нажми на меня</a>"
        
        return "Произошла ошибка при создании конфигурации. Обратитесь в тех. поддержку."

    async def add_user(self, telegram_id: int, username: str | None):
        return self.user_repo.add_user(telegram_id, username)

    async def check_free_server(self):
        return self.server_repo.get_free_server()
    
    async def get_configuration(self, telegram_id: int):
        user = self.user_repo.get_user(telegram_id)
        if not user:
            return "Произошла ошибка при получении конфигурации. Обратитесь в тех. поддержку."
        url = f"https://ronix-red.ru/api/user-data.php?userId={user.id}"
        text = f"<b>Вот ваша конфигурация 😎</b>\n\n🔗 Нажми на ссылку, чтобы импортировать конфиг в Hiddify:\n\n{url}\n\nИспользуйте её для подключения. Если что-то не работает, свяжитесь с поддержкой."

        return text