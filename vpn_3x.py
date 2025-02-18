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
        try:
            db = next(get_db())
            server_repo = ServerRepository(db)
            server = server_repo.get_free_server()
            if not server:
                print("Server not found")
                return None

            token = VPNService.get_auth_token(server)
            return token, server

        except Exception as e:
            print(f"Error working with database or server: {e}")
            return None

    @staticmethod
    def add_vpn_user(user_data):
        result = VPNService.find_api_url()
        if not result:
            return None, "No available servers"
        
        token, server = result
        email = user_data.get("username")
        uuid = str(user_data.get("id"))
        tg_id = user_data.get("tgId")
        subscription_end = datetime.strptime(user_data.get("subscription_end"), "%Y-%m-%d").timestamp() * 1000

        url = f"{server.server_address}:{server.server_port}/{server.server_sub}/panel/api/inbounds/addClient"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cookie": f"3x-ui={token}"
        }

        settings_data = {
            "clients": [
                {
                    "id": uuid,
                    "flow": "xtls-rprx-vision",
                    "email": email,
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": subscription_end,
                    "enable": True,
                    "tgId": tg_id,
                }
            ]
        }

        payload = {
            "id": 1,
            "settings": json.dumps(settings_data)
        }

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False)
            if response.status_code == 200:
                print("Пользователь успешно добавлен на VPN.")
                return response.status_code, server.id
            else:
                print(f"Ошибка при добавлении пользователя: {response.status_code} - {response.text}")
                return None, response.text
        except Exception as e:
            print(f"Ошибка при отправке запроса: {e}")
            return None, str(e)

    @staticmethod
    def generate_vpn_url(uuid, server_id):
        try:
            db = next(get_db())
            server_repo = ServerRepository(db)
            server = server_repo.get_server_by_id(server_id)
            if not server:
                raise ValueError(f"Server not found: {server_id}")

            token = VPNService.get_auth_token(server)

            # Получаем данные конфигурации
            url = f"{server.server_address}:{server.server_port}/{server.server_sub}/panel/api/inbounds/get/1"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Cookie": f"3x-ui={token}"
            }

            response = requests.get(url, headers=headers, verify=False)
            if response.status_code != 200:
                raise Exception(f"Error while fetching data: {response.status_code}")

            data = response.json()
            client_data = data["obj"]["settings"]
            clients = json.loads(client_data)["clients"]
            obj_data = data["obj"]["streamSettings"]
            stream_data = json.loads(obj_data)["realitySettings"]

            client = next((client for client in clients if client["id"] == str(uuid)), None)
            if not client:
                raise ValueError(f"Client with UUID {uuid} not found")

            # Формируем URL для подключения
            flow = client["flow"]
            pbk = stream_data["settings"]["publicKey"]
            sni = stream_data["serverNames"][0]
            sid = stream_data["shortIds"][0]
            remark = client.get("remark", "RONIX-VPN")
            domain = server.server_address.replace("https://", "")

            vless_url = f"vless://{uuid}@{domain}:443?type=tcp&security=reality&pbk={quote_plus(pbk)}&fp=chrome&sni={quote_plus(sni)}&sid={sid}&spx=%2F&flow={flow}#{quote_plus(remark)}"

            return vless_url

        except Exception as e:
            print(f"Error generating VPN URL: {e}")
            return None

    @staticmethod
    def get_server_from_id(server_id):
        server = ServerRepository.get_server_by_id(server_id)
        if server:
            return server
        raise ValueError(f"Server not found: {server_id}")
    
    @staticmethod
    def syns_user(user):
        try:
            if not hasattr(user, "server_id") or not user.server_id:
                raise KeyError("server_id")

            db = next(get_db())
            server_repo = ServerRepository(db)
            server = server_repo.get_server_by_id(user.server_id)
            if not server:
                raise ValueError(f"Server not found: {user.server_id}")

            token = VPNService.get_auth_token(server)

            # Обновляем данные пользователя
            url = f"{server.server_address}:{server.server_port}/{server.server_sub}/panel/api/inbounds/updateClient/{user.id}"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Cookie": f"3x-ui={token}"
            }

            settings_data = {
                "clients": [
                    {
                        "id": str(user.id),
                        "flow": "xtls-rprx-vision",
                        "email": user.username,
                        "limitIp": 0,
                        "totalGB": 0,
                        "expiryTime": int(user.subscription_end.timestamp() * 1000) if user.subscription_end else 0,
                        "enable": user.status != "blocked",
                        "tgId": user.telegram_id,
                    }
                ]
            }

            payload = {
                "id": 1,
                "settings": json.dumps(settings_data)
            }

            response = requests.post(url, headers=headers, json=payload, verify=False)
            if response.status_code != 200:
                raise Exception(f"Error while updating user: {response.status_code}")

            print("User data successfully updated")
            return response.json()

        except Exception as e:
            print(f"Error updating user: {e}")
            raise