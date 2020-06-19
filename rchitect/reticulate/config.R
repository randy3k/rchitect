# patch reticulate::py_discover_config
getOption("rchitect.py_tools")$attach()

Sys.setenv(RETICULATE_PYTHON = import("sys")$executable)
Sys.setenv(RETICULATE_REMAP_OUTPUT_STREAMS = "0")

ns <- getNamespace("reticulate")

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

py_to_r.rchitect.types.RObject <- import("rchitect")$robject

registerS3method("py_to_r", "rchitect.types.RObject", py_to_r.rchitect.types.RObject, ns)


utils <- import("rchitect.utils")

r_to_py.PyObject <- function(x) {
    id <- reticulate::py_eval(utils$id_str(x), convert = FALSE)
    ctypes <- reticulate::import("ctypes")
    result <- reticulate::py_call(ctypes$cast, id, ctypes$py_object)
    reticulate::py_get_attr(result, "value")
}

registerS3method("r_to_py", "PyObject", r_to_py.PyObject, ns)
