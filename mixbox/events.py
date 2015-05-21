"""The events module contains code which supports the registration and emitting
of events.

"""
import collections

# Event handler functions
__handlers = collections.defaultdict(list)


# Binding events
EVENT_BINDINGS_PRE_BUILD    = "bindings:pre:build"
EVENT_BINDINGS_POST_BUILD   = "bindings:post:build"

# Binding-to-API events
EVENT_API_PRE_FROM_OBJ      = "api:pre:from_obj"
EVENT_API_POST_FROM_OBJ     = "api:post:from_obj"
EVENT_API_PRE_TO_OBJ        = "api:pre:to_obj"
EVENT_API_POST_TO_OBJ       = "api:post:to_obj"

# Dictionary events
EVENT_API_PRE_FROM_DICT      = "api:pre:from_dict"
EVENT_API_POST_FROM_DICT     = "api:post:from_dict"
EVENT_API_PRE_TO_DICT        = "api:pre:to_dict"
EVENT_API_POST_TO_DICT       = "api:post:to_dict"


def register_handler(event_name, func):
    """Registers `func` as a handler for the event `event_name`.

    """
    if not callable(func):
        raise TypeError("Event handler must be callable.")

    __handlers[event_name].append(func)


def handler(event_name):
    """Function decorator which registers the wrapped function as a event
    handler for the event `event_name`.

    """
    def decorator(func):
        register_handler(event_name, func)  # register the event handler
        return func
    return decorator


def emit(event_name, *args, **kwargs):
    """Emits an event by serially calling each registered event handler for
    the event `event_name`.

    """
    if event_name not in __handlers:
        return

    handlers = __handlers[event_name]

    for func in handlers:
        func(*args, **kwargs)
