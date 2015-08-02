# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
The signals module contains code which supports the registration of signal
handlers, as well as the emitting of signals.
"""
import collections
import logging
import threading
import weakref

from .vendor import six

try:
    from weakref import WeakMethod
except ImportError:
    from weakrefmethod import WeakMethod


# Module-level logger
LOG = logging.getLogger(__name__)

# Signal receiver functions
__receivers = collections.defaultdict(list)

# Synchronize access to __receivers
__lock = threading.Lock()


def __is_dead(ref):
    """Return ``True`` if the weak reference `ref` no longer points to an
    in-memory object.
    """
    return ref() is None


def __make_id(receiver):
    """Generate an identifier for a signal receiver function/method.

    This is used when disconnecting receivers, where we need to correctly
    establish equivalence between the input receiver and the receivers assigned
    to a signal.
    """
    if __is_bound_method(receiver):
        return (id(receiver.__func__), id(receiver.__self__))
    return id(receiver)


def __purge():
    """Remove all dead signal receivers from the global receivers collection.

    Note:
        It is assumed that the caller holds the __lock.
    """
    global __receivers
    newreceivers = collections.defaultdict(list)

    for signal, receivers in six.iteritems(__receivers):
        alive = [x for x in receivers if not __is_dead(x)]
        newreceivers[signal] = alive

    __receivers = newreceivers


def __live_receivers(signal):
    """Return all signal handlers that are currently still alive for the
    input `signal`.

    Args:
        signal: A signal name.
    """
    with __lock:
        __purge()
        receivers = [funcref() for funcref in __receivers[signal]]

    return receivers


def __is_bound_method(method):
    """Return ``True`` if the `method` is a bound method (attached to an class
    instance.

    Args:
        method: A method or function type object.
    """
    if not(hasattr(method, "__func__") and hasattr(method, "__self__")):
        return False

    # Bound methods have a __self__ attribute pointing to the owner instance
    return six.get_method_self(method) is not None


def __check_receiver(func):
    """Check that the `func` is an acceptable signal receiver.

    Signal receivers must be one of the following:

    * Callable objects.
    * Bound instance methods
    * Static/class methods
    * Functions

    Raises:
        TypeError: If `func` is not an appropriate signal receiver.
    """
    if six.callable(func):
        return

    error = ("Signal receivers must be functions, callable objects, or "
             "static/class/bound methods.")
    raise TypeError(error)


def connect(signal_id, receiver):
    """Register `receiver` method/function as a receiver for the signal
    `signal_id`."""
    __check_receiver(receiver)

    if __is_bound_method(receiver):
        ref = WeakMethod
    else:
        ref = weakref.ref

    with __lock:
        __purge()
        __receivers[signal_id].append(ref(receiver))


def disconnect(signal_id, receiver):
    """Disconnect the receiver `func` from the signal, identified by
    `signal_id`.

    Args:
        signal_id: The signal identifier
        func: The receiver to disconnect
    """
    disconnected = False
    inputkey = __make_id(receiver)

    with __lock:
        __purge()
        receivers = __receivers.get(signal_id)

        for idx in six.moves.range(len(receivers)):
            connected = receivers[idx]()

            if inputkey == __make_id(connected):
                disconnected = True
                del receivers[idx]
                break

    return disconnected


def receiver(signal_id):
    """Function decorator which registers the wrapped function as a signal
    receiver for the signal `signal_name`.

    Warning:
        This will not work with unbound instance methods.
    """
    def decorator(func):
        connect(signal_id, func)  # register the signal receiver
        return func
    return decorator


def emit(signal_id, *args, **kwargs):
    """Emit a signal by serially calling each registered signal receiver for
    the signal `signal_name`.
    """
    if signal_id not in __receivers:
        return

    receivers = __live_receivers(signal_id)

    for func in receivers:
        func(*args, **kwargs)
