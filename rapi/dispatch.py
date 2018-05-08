from multipledispatch.dispatcher import Dispatcher, str_signature, MDNotImplementedError


class Type(type):
    instances = {}

    def __new__(cls, t):
        if type(t) == type:
            if t in cls.instances:
                return cls.instances[t]
            else:
                T = super(Type, cls).__new__(cls, "Type({})".format(t.__name__), (type,), {})
                cls.instances[t] = T
            return T
        else:
            return type(t)

    def __init__(self, t):
        self.t = t
        super(Type, self).__init__("Type({})".format(t.__name__), (type, ), {})

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
