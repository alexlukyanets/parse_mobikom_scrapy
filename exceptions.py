class ItemError(Exception):
    pass


class ItemValidationError(ItemError):
    pass


class ItemNormalizationError(ItemError):
    pass


class ValueConversionError(ItemError):
    pass
