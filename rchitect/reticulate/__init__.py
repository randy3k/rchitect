from __future__ import unicode_literals
import os
from rchitect.interface import rcall, rcopy, set_hook, package_event


def configure():
    def _configure():
        rcall(
            ("base", "source"),
            os.path.join(os.path.dirname(__file__), "config.R"),
            rcall(("base", "new.env")))

    if "reticulate" in rcopy(rcall(("base", "loadedNamespaces"))):
        _configure()
    else:
        set_hook(package_event("reticulate", "onLoad"), lambda x, y: _configure())
