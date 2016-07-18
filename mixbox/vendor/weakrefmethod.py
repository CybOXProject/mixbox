import weakref

"""NOTE: Remove this class in favor of using weakrefmethod as a dependency
once the PyPI version of the weakrefmethod module has the changes from
https://github.com/twang817/weakrefmethod/pull/4
"""

__all__ = ['WeakMethod']

class WeakMethod(weakref.ref):
    """
    A custom 'weakref.ref' subclass which simulates a weak reference to
    a bound method, working around the lifetime problem of bound methods
    """

    __slots__ = '_func_ref', '_meth_type', '_alive', '__weakref__'

    def __new__(cls, meth, callback=None):
        try:
            obj = meth.__self__
            func = meth.__func__
        except AttributeError:
            raise TypeError('argument should be a bound method, not {0}'.format(type(meth)))

        def _cb(arg):
            # The self-weakref trick is needed to avoid creating a reference cycle.
            self = self_wr()
            if self._alive:
                self._alive = False
                if callback is not None:
                    callback(self)
        self = weakref.ref.__new__(cls, obj, _cb)
        self._func_ref = weakref.ref(func, _cb)
        self._meth_type = type(meth)
        self._alive = True
        self_wr = weakref.ref(self)
        return self

    def __call__(self):
        obj = super(WeakMethod, self).__call__()
        func = self._func_ref()
        if obj is None or func is None:
            return None
        return self._meth_type(func, obj)

    def __eq__(self, other):
        if isinstance(other, WeakMethod):
            if not self._alive or not other._alive:
                return self is other
            return weakref.ref.__eq__(self, other) and self._func_ref == other._func_ref
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = weakref.ref.__hash__
