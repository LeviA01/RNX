from sqlalchemy.orm import Session
from app.database.models.models import Server
from sqlalchemy import func, Float

class ServerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_free_server(self):
        return self.db.query(Server).filter(
            Server.current_users < Server.max_users
        ).order_by(
            func.cast(Server.current_users, Float) / func.cast(Server.max_users, Float)
        ).first()
    
    def get_two_different_country_servers(self):   
        # Выбираем все свободные сервера, сортируя их по отношению текущих пользователей к максимальному количеству
        free_servers = self.db.query(Server).filter(
            Server.current_users < Server.max_users
        ).order_by(
            func.cast(Server.current_users, Float) / func.cast(Server.max_users, Float)
        ).all()

        # Для каждой страны выбираем первый (наименее нагруженный) сервер
        selected_servers = {}
        for server in free_servers:
            if server.country not in selected_servers:
                selected_servers[server.country] = server

        # Возвращаем список серверов, по одному для каждой страны
        return list(selected_servers.values())

 
    def get_server_by_id(self, server_id):
        print(f"Debug - received server_id: {server_id}, type: {type(server_id)}")  # Отладочная информация
        
        # Если server_id это строка в формате PostgreSQL массива
        if isinstance(server_id, str):
            # Убираем фигурные скобки и пробелы, затем разбиваем по запятой
            cleaned_str = server_id.strip('{}').strip()
            if not cleaned_str:  # Если строка пустая после очистки
                print(f"Warning: Empty server_id after cleaning: {server_id}")
                return None
                
            try:
                # Проверяем, является ли строка одиночным числом
                if cleaned_str.isdigit():
                    return self.db.query(Server).filter(Server.id == int(cleaned_str)).first()
                
                # Преобразуем строку '{1,2,3}' в список [1,2,3]
                id_list = [int(x.strip()) for x in cleaned_str.split(',') if x.strip()]
                if not id_list:  # Если список пустой
                    print(f"Warning: No valid IDs found in: {server_id}")
                    return None
                    
                print(f"Debug - parsed id_list: {id_list}")  # Отладочная информация
                return self.db.query(Server).filter(Server.id.in_(id_list)).all()
                
            except ValueError as e:
                print(f"Error parsing server_id: {server_id}, error: {e}")
                return None
                
        # Если server_id это список
        elif isinstance(server_id, list):
            if not server_id:  # Если список пустой
                print("Warning: Empty server_id list")
                return None
            return self.db.query(Server).filter(Server.id.in_(server_id)).all()
            
        # Если server_id это одиночное значение
        elif isinstance(server_id, (int, float)):
            return self.db.query(Server).filter(Server.id == int(server_id)).first()
            
        print(f"Warning: Unsupported server_id type: {type(server_id)}")
        return None

    def update_server_users(self, server_id: str, increment: bool = True):
        # Если server_id это список
        if isinstance(server_id, list):
            servers = self.get_server_by_id(server_id)
            success = True
            for server in servers:
                if increment and server.current_users < server.max_users:
                    server.current_users += 1
                elif not increment and server.current_users > 0:
                    server.current_users -= 1
                else:
                    success = False
            self.db.commit()
            return success
        else:
            # Если server_id это одиночное значение
            server = self.get_server_by_id(server_id)
            if server:
                if increment and server.current_users < server.max_users:
                    server.current_users += 1
                elif not increment and server.current_users > 0:
                    server.current_users -= 1
                self.db.commit()
                return True
            return False

    