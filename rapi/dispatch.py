from __future__ import unicode_literals

from multipledispatch.dispatcher import Dispatcher, str_signature, MDNotImplementedError


class DataType(type):
    def __instancecheck__(self, instance):
        return self.t == instance

    def __subclasscheck__(self, subclass):
        return isinstance(subclass, DataType) and self.t == subclass.t


_data_types = {}


def typeof(t):
    if isinstance(t, type):
        try:
            return _data_types[t]
        except KeyError:
            T = DataType(
                str("DataType.{}".format(t.__name__)),
                (type,),
                {"t": t, "__new__": lambda cls: cls.t})
            _data_types[t] = T
            setattr(DataType, t.__name__, T)
            return T
    else:
        return type(t)


namespace = dict()


class TypeDispatcher(Dispatcher):

    def __call__(self, *args, **kwargs):
        types = tuple([typeof(arg) for arg in args])
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
