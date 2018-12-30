from __future__ import unicode_literals

# much of the following mechanism is inspired by https://github.com/mrocklin/multipledispatch


AMBIGUITY = "Signature {} is ambiguous with {}. Define signature {} to resolve the ambiguity"


class datatype(type):
    """
    We introduce a `datatype` function to allow different values from `datatype(str)` and
    `datatype(int)`.
    """

    _datatypes = {}

    def __new__(cls, *args):
        if len(args) == 1:
            t = args[0]
            try:
                return cls._datatypes[t]
            except KeyError:
                T = datatype(
                    str("datatype.{}".format(t.__name__)),
                    (type,),
                    {"t": t, "__new__": lambda cls: cls.t})
                cls._datatypes[t] = T
                setattr(datatype, t.__name__, T)
                return T
        else:
            return super(datatype, cls).__new__(cls, *args)

    def __instancecheck__(self, instance):
        return self.t == instance

    def __subclasscheck__(self, subclass):
        return isinstance(subclass, datatype) and self.t == subclass.t


def typeof(t):
    if isinstance(t, type):
        return datatype(t)
    else:
        return type(t)


def expand_tuples(L):
    """
    >>> expand_tuples([1, (2, 3)])
    [(1, 2), (1, 3)]
    >>> expand_tuples([1, 2])
    [(1, 2)]
    """
    if not L:
        return [()]
    elif not isinstance(L[0], tuple):
        rest = expand_tuples(L[1:])
        return [(L[0],) + t for t in rest]
    else:
        rest = expand_tuples(L[1:])
        return [(item,) + t for t in rest for item in L[0]]


def isstrictsubclass(a, b):
    return a != b and issubclass(a, b)


class Dispatcher(object):
    def __init__(self):
        self._cache = {}
        self._ordering = []
        self.funcs = {}

    def __call__(self, *args, **kwargs):
        types = tuple([typeof(arg) for arg in args])
        try:
            func = self._cache[types]
        except KeyError:
            func = self.dispatch(*types)
            if not func:
                raise NotImplementedError("Dispatch not found for signature %s" % str(*types))
            self._cache[types] = func
        return func(*args, **kwargs)

    @property
    def ordering(self):
        return self._ordering

    def reorder(self, types):
        if types in self._ordering:
            raise TypeError("Signature %s redefined" % str(*types))

        n = len(types)
        for signature in self._ordering:
            if len(signature) != n:
                continue
            if not any(map(isstrictsubclass, types, signature)) or \
                    not any(map(isstrictsubclass, signature, types)):
                continue
            parent = tuple(types[i] if issubclass(types[i], signature[i]) else signature[i]
                           for i in range(len(types)))
            if parent not in self._ordering:
                raise TypeError(
                    AMBIGUITY.format(
                        str(types),
                        str(signature),
                        str(parent)))

        p = 0
        for signature in self._ordering:
            if len(signature) == n and all(map(issubclass, types, signature)):
                break
            p = p + 1
        self._ordering.insert(p, types)

    def add(self, types, func):
        # support union types
        if any(isinstance(typ, tuple) for typ in types):
            for typs in expand_tuples(types):
                self.add(typs, func)
            return

        self.reorder(types)
        self._cache.clear()
        self.funcs[types] = func

    def dispatch(self, *types):
        if types in self.funcs:
            return self.funcs[types]
        try:
            return next(self.dispatch_iter(*types))
        except StopIteration:
            return None

    def dispatch_iter(self, *types):
        n = len(types)
        for signature in self.ordering:
            if len(signature) == n and all(map(issubclass, types, signature)):
                result = self.funcs[signature]
                yield result


namespace = dict()


def dispatch(*types):

    types = tuple(types)

    def _(func):
        name = func.__name__
        if name not in namespace:
            namespace[name] = Dispatcher()

        dispatcher = namespace[name]
        dispatcher.add(types, func)
        return dispatcher
    return _
