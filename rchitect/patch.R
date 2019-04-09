py_tools <- getOption("rchitect_py_tools")

import <- py_tools$import
import_builtins <- py_tools$import_builtins
py_call <- py_tools$py_call
py_eval <- py_tools$py_eval
py_copy <- py_tools$py_copy
tuple <- py_tools$tuple
dict <- py_tools$dict
`$.PyObject` <- py_tools$`$.PyObject`
`[.PyObject` <- py_tools$`[.PyObject`

py_config <- import("radian.py_config")
native_config <- py_copy(py_config$config())

reticulate_ns <- getNamespace("reticulate")

unlockBinding("py_discover_config", reticulate_ns)

old_py_discover_config <- reticulate_ns$py_discover_config

assign(
    "py_discover_config",
    function(...) {
        config <- old_py_discover_config(...)
        config$python <- native_config[[1]]
        config$libpython <- native_config[[2]]
        config
    },
    reticulate_ns)

lockBinding("py_discover_config", reticulate_ns)
