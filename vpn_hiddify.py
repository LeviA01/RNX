import urllib3
import json
import requests
from datetime import datetime
from urllib.parse import quote_plus
from app.database.connection import get_db
from app.database.repositories.server_repo import ServerRepository

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VPNService:
    @staticmethod
    def get_auth_token(server):
        """Получение токена авторизации для сервера"""
        try:
            login_url = f"{server.server_address}:{server.server_port}/{server.server_sub}/login"
            login_payload = {
                "username": server.login,
                "password": server.password
            }
            

            login_response = requests.post(login_url, json=login_payload, timeout=30, verify=False)
            
            if login_response.status_code == 200:
                token = login_response.cookies.get('3x-ui')
                if not token:
                    raise ValueError("Авторизация успешна, но токен не получен")
                return token
            else:
                raise Exception(f"Ошибка авторизации: {login_response.status_code, login_response.text}")
                
        except Exception as e:
            print(f"Ошибка при получении токена: {e}")
            raise

    @staticmethod
    def find_api_url():
        """Находит свободный сервер"""
        try:
            db = next(get_db())
            server_repo = ServerRepository(db)
            server = server_repo.get_free_server()
            if server:
                return server
            print("Server not found")
            return None
        except Exception as e:
            print(f"Error working with database or server: {e}")
            return None

    @staticmethod
    def check_server_connection(server):
        """Проверяет валидность API-ключа через простой запрос"""
        try:
            check_url = f"{server.server_address}/{server.server_sub}/api/v2/admin/system/"
            headers = {
                "Accept": "application/json",
                "Hiddify-API-Key": server.api
            }
            response = requests.get(check_url, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                print("Сервер доступен и API-ключ валиден")
                return True
            else:
                print(f"Ошибка подключения: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            return False

    @staticmethod
    def add_vpn_user(user_data):
        """Добавляет нового VPN пользователя"""
        db = next(get_db())
        server_repo = ServerRepository(db)
        server = server_repo.get_free_server()
        if not server:
            return None, "No available servers"

        url = f"{server.server_address}/{server.server_sub}/api/v2/admin/user/"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Hiddify-API-Key": server.api
        }

        subscription_end = datetime.strptime(user_data.get("subscription_end"), "%Y-%m-%d").date()
        
        payload = {
            "name": user_data.get("username"),
            "telegram_id": user_data.get("tgId"),
            "usage_limit_GB": 200,
            "package_days": (subscription_end - datetime.now().date()).days,
            "start_date": datetime.now().date().isoformat(),
            "uuid": str(user_data.get("id")),
            "enable": True,
            "is_active": True,
            "mode": "monthly",
            "lang": "ru",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Пользователь успешно добавлен в Hiddify")
                return response.status_code, server.id
            else:
                print(f"Ошибка при добавлении пользователя: {response.status_code}")
                print("Ответ сервера:", response.text)
                return None, response.text
        except Exception as e:
            print(f"Ошибка при отправке запроса: {e}")
            return None, str(e)

    @staticmethod
    def generate_vpn_url(uuid, server_id):
        """Генерирует URL для подключения к VPN"""
        try:
            db = next(get_db())
            server_repo = ServerRepository(db)
            server = server_repo.get_server_by_id(server_id)
            if not server:
                raise ValueError(f"Server not found: {server_id}")
            
            return f"{server.server_address}/{server.user_api}/{uuid}/#RONIX-VPN"
        except Exception as e:
            print(f"Error generating VPN URL: {e}")
            return None

    @staticmethod
    def get_server_from_id(server_id):
        """Получает сервер по ID"""
        db = next(get_db())
        server_repo = ServerRepository(db)
        server = server_repo.get_server_by_id(server_id)
        if server:
            return server
        raise ValueError(f"Server not found: {server_id}")

    @staticmethod
    def syns_user(user):
        """Синхронизирует данные пользователя"""
        try:
            if not hasattr(user, "server_id") or not user.server_id:
                raise KeyError("server_id")

            db = next(get_db())
            server_repo = ServerRepository(db)
            server = server_repo.get_server_by_id(user.server_id)
            if not server:
                raise ValueError(f"Server not found: {user.server_id}")

            url = f"{server.server_address}/{server.server_sub}/api/v2/admin/user/{user.id}/"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Hiddify-API-Key": server.api
            }

            package_days = (user.subscription_end.date() - datetime.now().date()).days if user.subscription_end else 0

            payload = {
                "name": user.username,
                "telegram_id": user.telegram_id,
                "usage_limit_GB": 200,
                "package_days": package_days,
                "start_date": datetime.now().date().isoformat(),
                "mode": "monthly",
                "lang": "ru",
                "enable": user.status != "blocked",
                "is_active": user.status != "blocked",
                "uuid": str(user.id),
                "current_usage_GB": 0,
                "last_reset_time": None
            }

            response = requests.patch(url, headers=headers, json=payload, verify=False, timeout=10)
            
            if response.status_code not in (200, 204):
                error_msg = f"Ошибка обновления: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)

            print("Данные пользователя успешно обновлены")
            return response.json()

        except KeyError as e:
            error_msg = f"Отсутствует обязательное поле: {e}"
            print(error_msg)
            raise
        except Exception as e:
            print(f"Ошибка при обновлении пользователя: {e}")
            raise