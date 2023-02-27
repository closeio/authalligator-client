import datetime
import enum
import re
import time
from typing import Any, Dict

import attr


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase.

    Adapted from this response in Stackoverflow:
        http://stackoverflow.com/a/19053800/1072990
    """
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


# pre-compile regexes
_to_snake_case_regex_1 = re.compile("(.)([A-Z][a-z]+)")
_to_snake_case_regex_2 = re.compile("([a-z0-9])([A-Z])")


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case.

    From this response in Stackoverflow:
        http://stackoverflow.com/a/1176023/1072990
    """
    s1 = _to_snake_case_regex_1.sub(r"\1_\2", name)
    return _to_snake_case_regex_2.sub(r"\1_\2", s1).lower()


def as_json_dict(obj: Any) -> Dict:
    """
    Similar to attr.asdict, but will prioritize an `as_dict` instance method
    over ``attr.asdict`` (if present) on nested objects and tries to convert
    common python types to json-encodable values.

    Ex: datetimes are converted to isoformat, enums are converted to their
    values, etc.

    Expected Usage::

        @attr.s
        class MyClass(object):
            a = attr.ib()

            as_dict = as_json_dict

        # ... later
        my_dict = MyClass(a=x).as_dict()

    Note the caveat that ``as_json_dict(my_class)`` won't equal
    ``my_class.as_dict()`` if ``my_class`` defines custom logic within an
    overridden ``as_dict`` method.

    :param obj: attrs object to convert to a dictionary. Optionally can be
        a dictionary, which will recursively serialize keys/values the same
        way.
    :returns: a dict
    """
    if isinstance(obj, dict):
        ret = obj
    else:
        ret = attr.asdict(obj, recurse=False)  # handling recursing manually

    for k, v in ret.items():
        if isinstance(v, datetime.datetime):
            ret[k] = v.isoformat()
        elif isinstance(v, enum.Enum):
            ret[k] = v.value
        elif isinstance(v, (list, tuple, set)):
            ret[k] = [(as_json_dict(i) if attr.has(i.__class__) else i) for i in v]
        elif isinstance(v, dict):
            ret[k] = as_json_dict(v)
        elif attr.has(v.__class__):
            if callable(getattr(v, "as_dict", None)):
                ret[k] = v.as_dict()
            else:
                ret[k] = as_json_dict(v)

    return ret


def retry(exc=Exception, tries=1, wait=0):
    """
    A way to retry a function call up to [tries] times if it throws
    a [exc] exception, with [wait] seconds in between.

    Can be used as a decorator factory.

    Example Usage:
        @retry(exc=ValueError, tries=10, wait=0.3)
        def unreliable_function(foo):
            # ...
        unreliable_function('boy')
    """

    def decorator(func):
        def _retry(*args, **kwargs):
            tries_left = tries
            while True:
                try:
                    return func(*args, **kwargs)
                except exc:
                    tries_left -= 1
                    if tries_left <= 0:
                        raise
                    time.sleep(wait)

        return _retry

    return decorator
