import socket

def send_signal(host: str, message: str, port: int = 6722, timeout: float = 1.0) -> str:
    """
    Отправляет TCP-сообщение на плату и возвращает ответ (первые 2 символа).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.sendall(message.encode())
        sock.shutdown(socket.SHUT_WR)
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
    return response.decode()[:2]

def check_board(ip: str) -> dict:
    """
    Проверяет доступность платы и возвращает состояния реле.
    Возвращает словарь: {'available': bool, 'relay1': bool|None, 'relay2': bool|None}
    """
    try:
        state_str = send_signal(ip, '00')   # запрос состояния без действий
        # Парсим ответ: первый символ – реле1, второй – реле2
        relay1 = (state_str[0] == '1')
        relay2 = (state_str[1] == '1')
        return {'available': True, 'relay1': relay1, 'relay2': relay2}
    except Exception:
        return {'available': False, 'relay1': None, 'relay2': None}
    
def try_reconnect(board):
    """Пытается восстановить связь с платой, если она была недоступна.
    Возвращает True, если плата теперь доступна (или была доступна ранее).
    """
    if board.is_available:
        return True  # уже доступна
    # Пытаемся проверить доступность
    status = check_board(board.ip_address)
    if status['available']:
        board.is_available = True
        board.relay1_state = status['relay1']
        board.relay2_state = status['relay2']
        board.save()
        return True
    return False