import sys


def append_path(x):
    if x not in sys.path:
        sys.path.append(x)
