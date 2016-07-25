# Copyright (c) 2015, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.
"""
The signals module contains code which supports the registration of signal
handlers, as well as the emitting of signals.

Attribution:
    Much of the code here was inspired by Django signals:
    https://github.com/django/django/blob/1.8.3/django/dispatch/dispatcher.py
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
    """Generate an identifier for a callable signal receiver.

    This is used when disconnecting receivers, where we need to correctly
    establish equivalence between the input receiver and the receivers assigned
    to a signal.

    Args:
        receiver: A callable object.

    Returns:
        An identifier for the receiver.
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

    Returns:
        A list of callable receivers for the input signal.
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


def __check_receiver(receiver):
    """Check that the `receiver` is an acceptable signal receiver.

    Signal receivers must be one of the following:

    * Callable objects.
    * Bound instance methods
    * Static/class methods
    * Functions

    Raises:
        TypeError: If `func` is not an appropriate signal receiver.
    """
    if six.callable(receiver):
        return

    error = ("Signal receivers must be functions, callable objects, or "
             "static/class/bound methods.")
    raise TypeError(error)


def connect(signal, receiver):
    """Register `receiver` method/function as a receiver for the `signal`.

    When the signal is emitted, this receiver will be invoked along with
    all other associated signals.

    Args:
        signal: A signal identifier (e.g., a signal name)
        receiver: A callable object to connect to the signal.
    """
    __check_receiver(receiver)

    if __is_bound_method(receiver):
        ref = WeakMethod
    else:
        ref = weakref.ref

    with __lock:
        __purge()
        __receivers[signal].append(ref(receiver))


def disconnect(signal, receiver):
    """Disconnect the receiver `func` from the signal, identified by
    `signal_id`.

    Args:
        signal: The signal identifier.
        receiver: The callable receiver to disconnect.

    Returns:
        True if the receiver was successfully disconnected. False otherwise.
    """
    inputkey = __make_id(receiver)

    with __lock:
        __purge()
        receivers = __receivers.get(signal)

        for idx in six.moves.range(len(receivers)):
            connected = receivers[idx]()

            if inputkey != __make_id(connected):
                continue

            del receivers[idx]
            return True  # receiver successfully disconnected!

    return False


def receiver(signal):
    """Function decorator which registers the wrapped function as a signal
    receiver for the signal `signal_name`.

    Warning:
        This will not work with unbound instance methods.

    Args:
        signal: A signal identifier (e.g., a name).
    """
    def decorator(func):
        connect(signal, func)  # register the signal receiver
        return func
    return decorator


def emit(signal, *args, **kwargs):
    """Emit a signal by serially calling each registered signal receiver for
    the `signal`.

    Note:
        The receiver must accept the *args and/or **kwargs that have been
        passed to it. There expected parameters are not dictated by
        mixbox.
        
    Args:
        signal: A signal identifier or name.
        *args: A variable-length argument list to pass to the receiver.
        **kwargs: Keyword-arguments to pass to the receiver.
    """
    if signal not in __receivers:
        return

    receivers = __live_receivers(signal)

    for func in receivers:
        func(*args, **kwargs)
