from rchitect import reval, rcopy
from rchitect._cffi import lib, ffi
import sys
import pytest


@pytest.mark.skipif(not sys.platform.startswith("win") and not sys.stdout.isatty(), reason="not tty")
def test_read_console(mocker, gctorture):
    mocker.patch("rchitect.callbacks.ask_input", return_value="hello")
    ret = reval("readline('> ')")
    assert rcopy(ret) == "hello"


@pytest.mark.skipif(not sys.platform.startswith("win") and not sys.stdout.isatty(), reason="not tty")
def test_read_console_long(mocker, gctorture):
    for h in [2000, 4094, 4095, 4096, 4097, 5000]:
        s = "b" * h
        mocker.patch("rchitect.callbacks.ask_input", return_value=s)
        ret = reval("readline('> ')")
        assert rcopy(ret) == s
        assert len(rcopy(ret)) == len(s)


def test_read_console_long_utf8(mocker, gctorture):
    mocker.patch("rchitect.callbacks.utf8tosystem", side_effect=lambda x: x.encode("utf-8"))
    for offset in [0, 1, 2]:
        s = ("a" * offset) + ("文字" * 1000)
        mocker.patch("rchitect.callbacks.ask_input", return_value=s)
        buf = ffi.new("char[4096]")
        chunks = []
        while True:
            lib.cb_read_console(ffi.new("char[]", b"> "), buf, 4096, 0)
            chunk = ffi.string(buf).decode("utf-8")
            chunks.append(chunk)
            if chunk.endswith("\n"):
                break
        assert "".join(chunks) == s + "\n"



@pytest.mark.skipif(not sys.platform.startswith("win") and not sys.stdout.isatty(), reason="not tty")
def test_read_console_interrupt(mocker, gctorture):
    mocker.patch("rchitect.callbacks.ask_input", side_effect=KeyboardInterrupt())
    with pytest.raises(Exception) as excinfo:
        reval("readline('> ')")
    assert str(excinfo.value).startswith("Error")


def test_write_console(mocker, gctorture):
    mocker_write_console = mocker.patch("rchitect.console.write_console")
    reval("cat('helloworld')")
    mocker_write_console.assert_called_once_with('helloworld', 0)


def test_write_console_utf8(mocker, gctorture):
    mocker_write_console = mocker.patch("rchitect.console.write_console")
    # windows still doesn't like `𐐀`
    reval("cat('文字')")
    mocker_write_console.assert_called_once_with('文字', 0)


def test_write_console_stderr(mocker, gctorture):
    mocker_write_console = mocker.patch("rchitect.console.write_console")
    reval("cat('helloworld', file = stderr())")
    mocker_write_console.assert_called_once_with('helloworld', 1)


def test_write_console_worker_thread(mocker, gctorture):
    import threading

    mocker_write_console_ex = mocker.patch("rchitect.callbacks.callback.write_console_ex")
    mocker_busy = mocker.patch("rchitect.callbacks.callback.busy")
    mocker_polled_events = mocker.patch("rchitect.callbacks.callback.polled_events")

    def worker():
        out_buf = ffi.new("char[]", b"worker stdout\n")
        err_buf = ffi.new("char[]", b"worker stderr\n")
        lib.cb_write_console_ex_safe(out_buf, 14, 0)
        lib.cb_write_console_ex_safe(err_buf, 14, 1)
        lib.cb_busy_safe(1)
        lib.cb_polled_events_safe()

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    # Worker thread output is queued, not written from the worker thread
    mocker_write_console_ex.assert_not_called()
    mocker_busy.assert_not_called()
    mocker_polled_events.assert_not_called()

    # Main thread flushes the queued worker output in order along with its own output
    reval("cat('main thread')")
    assert mocker_write_console_ex.call_args_list == [
        mocker.call("worker stdout\n", 0),
        mocker.call("worker stderr\n", 1),
        mocker.call("main thread", 0),
    ]

    # Verify GIL is released during reval so a worker thread can call cb_write_console_ex_safe
    # while R is executing without deadlocking
    mocker_write_console_ex.reset_mock()
    worker_done = threading.Event()

    def concurrent_worker():
        buf = ffi.new("char[]", b"during reval\n")
        lib.cb_write_console_ex_safe(buf, 13, 0)
        worker_done.set()

    t2 = threading.Thread(target=concurrent_worker)
    t2.start()
    reval("Sys.sleep(0.05)")
    t2.join(timeout=1.0)
    assert worker_done.is_set()
    assert mocker_write_console_ex.call_args_list == [
        mocker.call("during reval\n", 0),
    ]

    # Verify worker output does not contaminate RObject.__repr__ or RuntimeError messages
    obj = reval("1L")
    mocker_write_console_ex.reset_mock()
    t3 = threading.Thread(target=worker)
    t3.start()
    t3.join()
    assert "worker stdout" not in repr(obj)
    assert mocker_write_console_ex.call_args_list == [
        mocker.call("worker stdout\n", 0),
        mocker.call("worker stderr\n", 1),
    ]

    # Verify dropping an RObject reference on a worker thread defers release to the main thread
    holder = [reval("c(1L, 2L, 3L)")]
    del obj

    def release_on_worker():
        holder.clear()

    t4 = threading.Thread(target=release_on_worker)
    t4.start()
    t4.join()
    assert rcopy(reval("1L + 1L")) == 2


@pytest.mark.skipif(sys.platform.startswith("win"), reason="fork not supported on Windows")
def test_fork_xptr_finalizer():
    import os
    import threading
    from rchitect import rcall, robject

    parent_pid = os.getpid()
    r_fd, w_fd = os.pipe()
    os.set_blocking(r_fd, False)

    def read_pids():
        try:
            data = os.read(r_fd, 4096)
        except BlockingIOError:
            return []
        return [int(x) for x in data.decode("ascii").splitlines() if x]

    class TrackedResource(object):
        def __del__(self):
            try:
                os.write(w_fd, "{}\n".format(os.getpid()).encode("ascii"))
            except OSError:
                pass

    stop_bg = threading.Event()

    def bg_gil_worker():
        while not stop_bg.is_set():
            _ = sum(range(100))

    bg = threading.Thread(target=bg_gil_worker)
    bg.start()
    try:
        rcall(("base", "assign"), "tracked_res", robject("PyObject", TrackedResource()))
        res = rcopy(
            reval(
                "parallel::mclapply(1:2, function(i) {"
                "  rm(tracked_res, envir = .GlobalEnv);"
                "  gc();"
                "  i"
                "}, mc.cores = 2)"
            )
        )
        assert res == [1, 2]
        assert read_pids() == []

        reval("rm(tracked_res, envir = .GlobalEnv); gc()")
        assert read_pids() == [parent_pid]
    finally:
        stop_bg.set()
        bg.join(timeout=1.0)
        os.close(r_fd)
        os.close(w_fd)





def test_yes_no_cancel(mocker, gctorture):
    for (a, v) in [('y', 1), ('n', 2), ('c', 0)]:
        mocker.patch("rchitect.callbacks.ask_input", return_value=a)
        ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
        assert ret == v
    mocker.resetall()


def test_yes_no_cancel_exceptions(mocker, gctorture):
    count = [0]

    def throw_on_first_run(_):
        if count[0] == 0:
            count[0] += 1
            raise Exception()
        else:
            return "y"

    mocker.patch("rchitect.callbacks.ask_input", side_effect=throw_on_first_run)
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 1

    mocker.patch("rchitect.callbacks.ask_input", side_effect=EOFError())
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 0

    mocker.patch("rchitect.callbacks.ask_input", side_effect=KeyboardInterrupt())
    ret = lib.cb_yes_no_cancel(ffi.new("char[10]", b"> "))
    assert ret == 0
