from __future__ import unicode_literals
import os
import sys
from rchitect.interface import rcall, rcopy, set_hook, package_event


def configure():
    def _configure():
        # os.environ doesn't set the variables in C, we'll need to either use
        # `msvcrt._putenv` or to use the R function `Sys.setenv`.
        # os.environ["RETICULATE_PYTHON"] = sys.executable
        # os.environ["RETICULATE_REMAP_OUTPUT_STREAMS"] = "0"
        rcall(("base", "Sys.setenv"),
              RETICULATE_PYTHON=sys.executable,
              RETICULATE_REMAP_OUTPUT_STREAMS="0")

        rcall(
            ("base", "source"),
            os.path.join(os.path.dirname(__file__), "config.R"),
            rcall(("base", "new.env")))

    if "reticulate" in rcopy(rcall(("base", "loadedNamespaces"))):
        _configure()
    else:
        set_hook(package_event("reticulate", "onLoad"), lambda x, y: _configure())
