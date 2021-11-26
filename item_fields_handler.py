import datetime
import json
import logging
import re

from .exceptions import ValueConversionError
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
        if len(cleared_value) >= 3 and value[-3] in (',', '.'):
            cleared_value = cleared_value[:-3] + '$' + cleared_value[-2:]
        elif len(cleared_value) >= 2 and value[-2] in (',', '.'):
            cleared_value = cleared_value[:-2] + '$' + cleared_value[-1:]
        cleaned_value = cleared_value.replace('.', '').replace(',', '').replace('$', '.')
        try:
            return float(cleaned_value)
        except ValueError:
            logger.error(f'The value "{value}" can not be converted to float')
            return

    @classmethod
    def deserialize(cls, value):
        try:
            return json.loads(value)
        except (TypeError, json.decoder.JSONDecodeError):
            raise ValueConversionError('The JSON value can not be deserialized')
