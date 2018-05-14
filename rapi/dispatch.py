from __future__ import unicode_literals

from multipledispatch.dispatcher import Dispatcher, str_signature, MDNotImplementedError


class Type(type):
    _instances = {}

    def __new__(cls, t):
        if isinstance(t, type) and t is not object:
            if t in cls._instances:
                return cls._instances[t]
            else:
                T = super(Type, cls).__new__(
                    cls, str("Type({})".format(t.__name__)),
                    (type,),
                    {"__new__": lambda cls: t})
                cls._instances[t] = T
            return T
        else:
            return type(t)

    def __init__(self, t):
        self.t = t

    def __instancecheck__(self, instance):
        return self.t == instance

    def __subclasscheck__(self, subclass):
        return isinstance(subclass, Type) and self.t == subclass.t


namespace = dict()


class TypeDispatcher(Dispatcher):

    def __call__(self, *args, **kwargs):
        types = tuple([Type(arg) for arg in args])
        try:
            func = self._cache[types]
        except KeyError:
            func = self.dispatch(*types)
            if not func:
                raise NotImplementedError(
                    'Could not find signature for %s: <%s>' %
                    (self.name, str_signature(types)))
            self._cache[types] = func
        try:
            return func(*args, **kwargs)

        except MDNotImplementedError:
            funcs = self.dispatch_iter(*types)
            next(funcs)  # burn first
            for func in funcs:
                try:
                    return func(*args, **kwargs)
                except MDNotImplementedError:
                    pass

            raise NotImplementedError(
                "Matching functions for "
                "%s: <%s> found, but none completed successfully" % (
                    self.name, str_signature(types),
                ),
            )


def dispatch(*types):

    types = tuple(types)

    def _(func):
        name = func.__name__
        if name not in namespace:
            namespace[name] = TypeDispatcher(name)

        dispatcher = namespace[name]
        dispatcher.add(types, func)
        return dispatcher
    return _
