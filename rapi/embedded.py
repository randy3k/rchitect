from __future__ import unicode_literals

import sys
from ctypes import c_int, c_size_t, c_char, c_char_p, c_void_p, cast
from ctypes import POINTER, CFUNCTYPE, PYFUNCTYPE, Structure


class RStart(Structure):
    _fields_ = [
        ('R_Quiet', c_int),
        ('R_Slave', c_int),
        ('R_Interactive', c_int),
        ('R_Verbose', c_int),
        ('LoadSiteFile', c_int),
        ('LoadInitFile', c_int),
        ('DebugInitFile', c_int),
        ('RestoreAction', c_int),
        ('SaveAction', c_int),
        ('vsize', c_size_t),
        ('nsize', c_size_t),
        ('max_vsize', c_size_t),
        ('max_nsize', c_size_t),
        ('ppsize', c_size_t),
        ('NoRenviron', c_int),
        ('rhome', POINTER(c_char)),
        ('home', POINTER(c_char)),
        ('ReadConsole', c_void_p),
        ('WriteConsole', c_void_p),
        ('CallBack', c_void_p),
        ('ShowMessage', c_void_p),
        ('YesNoCancel', c_void_p),
        ('Busy', c_void_p),
        ('CharacterMode', c_int),
        ('WriteConsoleEx', c_void_p)
    ]


class RCallback(object):
    R_Suicide = None
    R_ShowMessage = None
    R_ReadConsole = None
    # R_WriteConsole = None
    R_WriteConsoleEx = None
    R_ResetConsole = None
    R_FlushConsole = None
    R_ClearerrConsole = None
    R_Busy = None
    R_CleanUp = None
    R_ShowFiles = None
    R_ChooseFile = None
    R_EditFile = None
    R_loadhistory = None
    R_savehistory = None
    R_addhistory = None
    R_EditFiles = None
    do_selectlist = None
    do_dataentry = None
    do_dataviewer = None
    R_ProcessEvents = None
    R_PolledEvents = None

    def __setattr__(self, name, value):
        if hasattr(self, name):
            super(RCallback, self).__setattr__(name, value)
        else:
            raise ValueError("{} is not a valid callback name".format(name))


callback = RCallback()
callbackptr = []


def set_callback(name, func):
    setattr(callback, name, func)


def start(libR, arguments=["rapi", "--quiet", "--no-save"], repl=False):
    argn = len(arguments)
    argv = (c_char_p * argn)()
    for i, a in enumerate(arguments):
        argv[i] = c_char_p(a.encode('utf-8'))

    if repl:
        if sys.platform.startswith("win"):
            libR.R_setStartTime()
            setup_callbacks_win32(libR)
            libR.R_set_command_line_arguments(argn, argv)
        else:
            libR.Rf_initialize_R(argn, argv)
            setup_callbacks_posix(libR)
    else:

        libR.Rf_initEmbeddedR(argn, argv)
        if sys.platform.startswith("win"):
            setup_callbacks_win32(libR)
        else:
            setup_callbacks_posix(libR)


def setup_callbacks_posix(libR):

    # ptr_R_Suicide

    if callback.R_ShowMessage:
        ptr_show_message = CFUNCTYPE(None, c_char_p)(callback.R_ShowMessage)
        callbackptr.append(ptr_show_message)
        c_void_p.in_dll(libR, 'ptr_R_ShowMessage').value = cast(ptr_show_message, c_void_p).value

    if callback.R_ReadConsole:
        # make sure it is not gc'ed
        ptr_read_console = \
            CFUNCTYPE(c_int, c_char_p, POINTER(c_char), c_int, c_int)(callback.R_ReadConsole)
        callbackptr(ptr_read_console)
        c_void_p.in_dll(libR, 'ptr_R_ReadConsole').value = cast(ptr_read_console, c_void_p).value

    if callback.R_WriteConsoleEx:
        c_void_p.in_dll(libR, 'ptr_R_WriteConsole').value = None
        ptr_write_console_ex = CFUNCTYPE(None, c_char_p, c_int, c_int)(callback.R_WriteConsoleEx)
        callbackptr.append(ptr_write_console_ex)
        c_void_p.in_dll(libR, 'ptr_R_WriteConsoleEx').value = cast(ptr_write_console_ex, c_void_p).value

    # ptr_R_ResetConsole
    # ptr_R_FlushConsole
    # ptr_R_ClearerrConsole

    if callback.R_Busy:
        ptr_r_busy = CFUNCTYPE(None, c_int)(callback.R_Busy)
        callbackptr.append(ptr_r_busy)
        c_void_p.in_dll(libR, 'ptr_R_Busy').value = cast(ptr_r_busy, c_void_p).value

    if callback.R_CleanUp:
        ptr = c_void_p.in_dll(libR, 'ptr_R_CleanUp')
        orig_cleanup = PYFUNCTYPE(None, c_int, c_int, c_int)(ptr.value)

        def _handler(save_type, status, runlast):
            callback.R_CleanUp(save_type, status, runlast)
            orig_cleanup(save_type, status, runlast)

        ptr_r_clean_up = PYFUNCTYPE(None, c_int, c_int, c_int)(_handler)
        callbackptr.append(ptr_r_clean_up)
        ptr.value = cast(ptr_r_clean_up, c_void_p).value

    # ptr_R_ShowFiles
    # ptr_R_ChooseFile
    # ptr_R_EditFile
    # ptr_R_loadhistory
    # ptr_R_savehistory
    # ptr_R_addhistory
    # ptr_R_EditFiles
    # ptr_do_selectlist
    # ptr_do_dataentry
    # ptr_do_dataviewer

    if callback.R_ProcessEvents:
        ptr_process_event = CFUNCTYPE(None)(callback.R_ProcessEvents)
        callbackptr.append(ptr_process_event)
        c_void_p.in_dll(libR, 'ptr_R_ProcessEvents').value = cast(ptr_process_event, c_void_p).value

    if callback.R_PolledEvents:
        ptr_polled_events = CFUNCTYPE(None)(callback.R_PolledEvents)
        callbackptr.append(ptr_polled_events)
        c_void_p.in_dll(libR, 'R_PolledEvents').value = cast(ptr_polled_events, c_void_p).value


def setup_callbacks_win32(libR):
    pass
