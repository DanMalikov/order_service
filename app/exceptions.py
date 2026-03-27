class OrderNotFoundError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


class NotEnoughQtyError(Exception):
    pass


class CatalogServiceUnavailableError(Exception):
    pass


class PaymentServiceUnavailableError(Exception):
    pass


class DuplicateInboxEventError(Exception):
    pass


class InvalidShippingEventError(Exception):
    pass
