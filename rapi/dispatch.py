from multipledispatch import dispatch as md_dispatch
from multipledispatch.dispatcher import Dispatcher


class Type(type):
    def __init__(self, t):
        self.t = t


namespace = dict()

@md_dispatch(object, Type, namespace=namespace)
def _issubclass(a, b):
    return a == b.t


@md_dispatch(object, object, namespace=namespace)
def _issubclass(a, b):
    return issubclass(a, b)


class TypeDispatcher(Dispatcher):

    def dispatch_iter(self, *types):
        n = len(types)
        for signature in self.ordering:
            if len(signature) == n and all(map(_issubclass, types, signature)):
                result = self.funcs[signature]
                yield result


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
