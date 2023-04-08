class UnavailableServer(Exception):
    """Ошибка о недоступности ENDPOINT."""

    pass


class Telegramerror():
    """Ошибка с отправкой сообщения в телеграм."""

    pass


class UnexpectedStatusError(Exception):
    """Ошибка со статусом работы."""

    pass
