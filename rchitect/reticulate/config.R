getOption("rchitect.py_tools")$attach()

ns <- getNamespace("reticulate")

# patch reticulate::py_discover_config

if (.Platform$OS.type == "unix") {
    py_config <- import("rchitect.py_config")
    native_config <- py_copy(py_config$config())

    unlockBinding("py_discover_config", ns)

    old_py_discover_config <- ns$py_discover_config

    assign(
        "py_discover_config",
        function(...) {
            "patched by rchitect"
            config <- old_py_discover_config(...)
            config$python <- native_config[[1]]
            config$libpython <- native_config[[2]]
            config
        },
        ns)

    lockBinding("py_discover_config", ns)
}

# conversions

utils <- import("rchitect.utils")

py_to_r.rchitect.types.RObject <- function(x) {
    utils$identity(x)  # triggers `rcopy` when callback is called
}

registerS3method("py_to_r", "rchitect.types.RObject", py_to_r.rchitect.types.RObject, ns)


r_to_py.PyObject <- function(x) {
    id <- reticulate::py_eval(utils$id_str(x), convert = FALSE)
    ctypes <- reticulate::import("ctypes")
    result <- reticulate::py_call(ctypes$cast, id, ctypes$py_object)
    reticulate::py_get_attr(result, "value")
}

registerS3method("r_to_py", "PyObject", r_to_py.PyObject, ns)
