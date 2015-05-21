# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
The signals module contains code which supports the registration of signal
handlers, as well as the emitting of signals.

"""
import collections

# Signal handler functions
__handlers = collections.defaultdict(list)


def register_handler(signal_name, func):
    """Registers `func` as a handler for the signal `signal_name`.

    """
    if not callable(func):
        raise TypeError("Signal handler must be callable.")

    __handlers[signal_name].append(func)


def handler(signal_name):
    """Function decorator which registers the wrapped function as a signal
    handler for the signal `signal_name`.

    """
    def decorator(func):
        register_handler(signal_name, func)  # register the signal handler
        return func
    return decorator


def emit(signal_name, *args, **kwargs):
    """Emits an signal by serially calling each registered signal handler for
    the signal `signal_name`.

    """
    if signal_name not in __handlers:
        return

    handlers = __handlers[signal_name]

    for func in handlers:
        func(*args, **kwargs)
