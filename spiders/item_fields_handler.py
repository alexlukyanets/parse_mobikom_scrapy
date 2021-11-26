import logging
import json

from parse_mobikom.spiders.exceptions import ValueConversionError
from urllib.parse import unquote_plus

logger = logging.getLogger(__name__)


class ItemFieldsHandler:

    @classmethod
    def clear_string(cls, value):
        if not isinstance(value, str):
            raise TypeError(f'The value "{value}" does not string type')
        value = unquote_plus(value)
        return ' '.join(value.split())

    @classmethod
    def convert_string_to_float(cls, value):
        if not isinstance(value, str):
            raise TypeError(f'The value "{value}" does not string type')
        cleared_value = value.replace('$', '').strip()
        try:
            return float(cleared_value)
        except ValueError:
            logger.error(f'The value "{value}" can not be converted to float')
            return

    @classmethod
    def deserialize(cls, value):
        try:
            return json.loads(value)
        except (TypeError, json.decoder.JSONDecodeError):
            raise ValueConversionError('The JSON value can not be deserialized')
