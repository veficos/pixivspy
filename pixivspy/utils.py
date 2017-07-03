# coding=utf-8
# author=veficos

from functools import wraps


class RetryExecute(Exception):
    pass


def retry_execute(count):
    def wrapper(fn):
        @wraps(fn)
        def execute(*args, **kwargs):
            for _ in range(count):
                try:
                    return fn(*args, **kwargs)
                except RetryExecute:
                    continue
        return execute
    return wrapper
