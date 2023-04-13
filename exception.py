class UnavailableServer(Exception):
    """Ошибка о недоступности ENDPOINT."""

    pass


class UnexpectedStatusError(Exception):
    """Ошибка со статусом работы."""

    pass
