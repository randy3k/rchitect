import importlib


__all__ = [
    "init",
    "loop",
    "def_callback",
    "undef_callback",
    "rparse",
    "reval",
    "rprint",
    "rlang",
    "rcall",
    "rcopy",
    "robject",
]

__version__ = "0.5.0.dev0"

_LAZY_ATTRS = {
    "init": ".setup",
    "loop": ".setup",
    "def_callback": ".callbacks",
    "undef_callback": ".callbacks",
    "rparse": ".interface",
    "reval": ".interface",
    "rprint": ".interface",
    "rlang": ".interface",
    "rcall": ".interface",
    "rcopy": ".interface",
    "robject": ".interface",
}

_SUBMODULES = {
    "setup",
    "callbacks",
    "interface",
    "completion",
    "console",
    "dispatch",
    "py_tools",
    "repl",
    "reticulate",
    "types",
    "utils",
    "xptr",
}


def __getattr__(name):
    if name in _LAZY_ATTRS:
        mod = importlib.import_module(_LAZY_ATTRS[name], __name__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    if name in _SUBMODULES:
        return importlib.import_module("." + name, __name__)
    raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name))
