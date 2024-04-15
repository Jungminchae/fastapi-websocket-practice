class MaximumSessionReachException(Exception):
    def __init__(self, message=None):
        super().__init__(message)

class MaximumConnectionPerSessionReachException(Exception):
    def __init__(self, message=None):
        super().__init__(message)


class WebSocketManager:
    MAX_SESSIONS = 1000
    MAX_CONNECTIONS_PER_SESSION = 10

    def __init__(self):
        self.connected_clients = {}

    def add_client(self, session_id, client):
        if len(self.connected_clients) >= self.MAX_SESSIONS:
            raise MaximumSessionReachException("세션이 꽉 찼습니다")

        if session_id not in self.connected_clients:
            self.connected_clients[session_id] = set()

        if len(self.connected_clients[session_id]) >= self.MAX_CONNECTIONS_PER_SESSION:
            raise MaximumConnectionPerSessionReachException("세션당 최대 연결 수를 초과했습니다")

        self.connected_clients[session_id].add(client)


    def remove_client(self, session_id, client):
        self.connected_clients[session_id].remove(client)

    def get_clients(self, session_id):
        return self.connected_clients.get(session_id, set())


ws_manager = WebSocketManager()