class OrderNotFoundError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


class NotEnoughQtyError(Exception):
    pass


class CatalogServiceUnavailableError(Exception):
    pass
