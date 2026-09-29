#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

typedef int (*Py_Main_t)(int argc, wchar_t **argv);

static wchar_t g_fake_base_exe[32768];
static DWORD (WINAPI *orig_GetModuleFileNameW)(HMODULE, LPWSTR, DWORD) = NULL;

static DWORD WINAPI hooked_GetModuleFileNameW(HMODULE hModule, LPWSTR lpFilename, DWORD nSize) {
    if (hModule == NULL && g_fake_base_exe[0] != L'\0') {
        size_t len = wcslen(g_fake_base_exe);
        if (nSize == 0) {
            return 0;
        }
        if (len >= nSize) {
            wmemcpy(lpFilename, g_fake_base_exe, nSize - 1);
            lpFilename[nSize - 1] = L'\0';
            SetLastError(ERROR_INSUFFICIENT_BUFFER);
            return nSize;
        }
        wmemcpy(lpFilename, g_fake_base_exe, len + 1);
        SetLastError(ERROR_SUCCESS);
        return (DWORD)len;
    }
    return orig_GetModuleFileNameW(hModule, lpFilename, nSize);
}

static void patch_iat_getmodulefilenamew(HMODULE hMod) {
    if (!hMod) return;
    BYTE *base = (BYTE *)hMod;
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return;
    DWORD import_rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (!import_rva) return;
    IMAGE_IMPORT_DESCRIPTOR *desc = (IMAGE_IMPORT_DESCRIPTOR *)(base + import_rva);
    for (; desc->Name != 0; desc++) {
        if (!desc->FirstThunk || !desc->OriginalFirstThunk) continue;
        IMAGE_THUNK_DATA *ilt = (IMAGE_THUNK_DATA *)(base + desc->OriginalFirstThunk);
        IMAGE_THUNK_DATA *iat = (IMAGE_THUNK_DATA *)(base + desc->FirstThunk);
        for (; ilt->u1.AddressOfData != 0; ilt++, iat++) {
            if (IMAGE_SNAP_BY_ORDINAL(ilt->u1.Ordinal)) continue;
            IMAGE_IMPORT_BY_NAME *ibn = (IMAGE_IMPORT_BY_NAME *)(base + ilt->u1.AddressOfData);
            if (strcmp((const char *)ibn->Name, "GetModuleFileNameW") == 0) {
                DWORD oldProt;
                if (VirtualProtect(&iat->u1.Function, sizeof(ULONG_PTR), PAGE_READWRITE, &oldProt)) {
                    if (!orig_GetModuleFileNameW) {
                        orig_GetModuleFileNameW = (DWORD (WINAPI *)(HMODULE, LPWSTR, DWORD))iat->u1.Function;
                    }
                    iat->u1.Function = (ULONG_PTR)hooked_GetModuleFileNameW;
                    VirtualProtect(&iat->u1.Function, sizeof(ULONG_PTR), oldProt, &oldProt);
                }
            }
        }
    }
}

static void set_env_win(const wchar_t *name, const wchar_t *val) {
    SetEnvironmentVariableW(name, val);
    _wputenv_s(name, val ? val : L"");
}

static int is_dir_win(const wchar_t *path) {
    if (!path || !path[0]) return 0;
    DWORD attr = GetFileAttributesW(path);
    return (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY));
}

static int is_file_win(const wchar_t *path) {
    if (!path || !path[0]) return 0;
    DWORD attr = GetFileAttributesW(path);
    return (attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY));
}

static int ends_with_icase_win(const wchar_t *s, const wchar_t *suffix) {
    size_t slen = wcslen(s);
    size_t suflen = wcslen(suffix);
    if (slen < suflen) return 0;
    return _wcsicmp(s + slen - suflen, suffix) == 0;
}

static int run_r_rhome_win(const wchar_t *rbinary, wchar_t *out, size_t out_cap) {
    wchar_t bin_buf[32768];
    if (!ends_with_icase_win(rbinary, L".exe") &&
        !ends_with_icase_win(rbinary, L".bat") &&
        !ends_with_icase_win(rbinary, L".cmd")) {
        _snwprintf_s(bin_buf, 32768, _TRUNCATE, L"%ls.exe", rbinary);
    } else {
        wcscpy_s(bin_buf, 32768, rbinary);
    }

    wchar_t found_path[32768];
    if (wcspbrk(bin_buf, L"\\/") != NULL) {
        if (!is_file_win(bin_buf) || !GetFullPathNameW(bin_buf, 32768, found_path, NULL)) {
            return 0;
        }
    } else if (!SearchPathW(NULL, bin_buf, NULL, 32768, found_path, NULL)) {
        return 0;
    }

    wchar_t saved_rhome[32768];
    DWORD had_rhome = GetEnvironmentVariableW(L"R_HOME", saved_rhome, 32768);
    if (had_rhome) {
        set_env_win(L"R_HOME", NULL);
    }

    wchar_t cmd[32768];
    _snwprintf_s(cmd, 32768, _TRUNCATE, L"\"\"%ls\" RHOME 2>NUL\"", found_path);

    int ok = 0;
    FILE *fp = _wpopen(cmd, L"r");
    if (fp) {
        if (fgetws(out, (int)out_cap, fp)) {
            size_t len = wcslen(out);
            while (len > 0 && (out[len - 1] == L'\r' || out[len - 1] == L'\n' || out[len - 1] == L' ')) {
                out[--len] = L'\0';
            }
            if (is_dir_win(out)) {
                ok = 1;
            }
        }
        _pclose(fp);
    }

    if (had_rhome) {
        set_env_win(L"R_HOME", saved_rhome);
    }
    return ok;
}

static int read_reg_install_path_win(HKEY root, const wchar_t *subkey, wchar_t *out, size_t out_cap) {
    HKEY hKey;
    if (RegOpenKeyExW(root, subkey, 0, KEY_READ, &hKey) != ERROR_SUCCESS) {
        return 0;
    }
    DWORD type = 0;
    DWORD bytes = (DWORD)(out_cap * sizeof(wchar_t));
    LSTATUS st = RegQueryValueExW(hKey, L"InstallPath", NULL, &type, (LPBYTE)out, &bytes);
    RegCloseKey(hKey);
    if (st == ERROR_SUCCESS && (type == REG_SZ || type == REG_EXPAND_SZ)) {
        size_t n = bytes / sizeof(wchar_t);
        if (n >= out_cap) {
            n = out_cap - 1;
        }
        out[n] = L'\0';
        if (is_dir_win(out)) {
            return 1;
        }
    }
    return 0;
}

static int read_registry_rhome_win(wchar_t *out, size_t out_cap) {
    if (read_reg_install_path_win(HKEY_CURRENT_USER, L"Software\\WOW6432Node\\R-Core\\R", out, out_cap)) return 1;
    if (read_reg_install_path_win(HKEY_LOCAL_MACHINE, L"Software\\WOW6432Node\\R-Core\\R", out, out_cap)) return 1;
    if (read_reg_install_path_win(HKEY_CURRENT_USER, L"Software\\R-Core\\R", out, out_cap)) return 1;
    if (read_reg_install_path_win(HKEY_LOCAL_MACHINE, L"Software\\R-Core\\R", out, out_cap)) return 1;
    return 0;
}

static int resolve_rhome_win(int argc, wchar_t **argv, wchar_t *rhome_out, size_t cap) {
    for (int i = 1; i < argc; i++) {
        if (wcsncmp(argv[i], L"--r-binary=", 11) == 0 && argv[i][11] != L'\0') {
            set_env_win(L"R_BINARY", argv[i] + 11);
        } else if (wcscmp(argv[i], L"--r-binary") == 0 && i + 1 < argc && argv[i + 1][0] != L'\0') {
            set_env_win(L"R_BINARY", argv[i + 1]);
            i++;
        }
    }

    wchar_t rbinary[32768];
    if (GetEnvironmentVariableW(L"R_BINARY", rbinary, 32768) && rbinary[0] != L'\0') {
        wchar_t cached_rhome[32768], cached_rbin[32768], cached_rh2[32768];
        if (GetEnvironmentVariableW(L"R_HOME", cached_rhome, 32768) &&
            GetEnvironmentVariableW(L"_RCHITECT_R_BINARY", cached_rbin, 32768) &&
            GetEnvironmentVariableW(L"_RCHITECT_R_HOME", cached_rh2, 32768) &&
            wcscmp(cached_rbin, rbinary) == 0 &&
            wcscmp(cached_rh2, cached_rhome) == 0 &&
            is_dir_win(cached_rhome)) {
            wcscpy_s(rhome_out, cap, cached_rhome);
            return 1;
        }
        if (run_r_rhome_win(rbinary, rhome_out, cap)) {
            set_env_win(L"R_HOME", rhome_out);
            set_env_win(L"_RCHITECT_R_BINARY", rbinary);
            set_env_win(L"_RCHITECT_R_HOME", rhome_out);
            return 1;
        }
        return 0;
    }

    if (GetEnvironmentVariableW(L"R_HOME", rhome_out, (DWORD)cap) && rhome_out[0] != L'\0') {
        return is_dir_win(rhome_out);
    }

    if (run_r_rhome_win(L"R.exe", rhome_out, cap) || read_registry_rhome_win(rhome_out, cap)) {
        set_env_win(L"R_HOME", rhome_out);
        return 1;
    }

    return 0;
}

static void setup_r_dll_win(const wchar_t *rhome) {
    wchar_t raw_dir[32768];
    wchar_t libr_dir[32768];
    wchar_t libr_path[32768];
#if defined(_M_ARM64) || defined(__aarch64__)
    _snwprintf_s(raw_dir, 32768, _TRUNCATE, L"%ls\\bin", rhome);
#else
    _snwprintf_s(raw_dir, 32768, _TRUNCATE, L"%ls\\bin\\x64", rhome);
#endif
    if (!GetFullPathNameW(raw_dir, 32768, libr_dir, NULL)) {
        wcscpy_s(libr_dir, 32768, raw_dir);
    }
    _snwprintf_s(libr_path, 32768, _TRUNCATE, L"%ls\\R.dll", libr_dir);
    if (!is_file_win(libr_path)) {
        return;
    }

    AddDllDirectory(libr_dir);

    wchar_t *env_path = (wchar_t *)malloc(65536 * sizeof(wchar_t));
    if (env_path) {
        DWORD len = GetEnvironmentVariableW(L"PATH", env_path, 65536);
        if (len == 0) {
            set_env_win(L"PATH", libr_dir);
        } else if (len < 65536 && !wcsstr(env_path, libr_dir)) {
            size_t new_cap = len + wcslen(libr_dir) + 4;
            wchar_t *new_path = (wchar_t *)malloc(new_cap * sizeof(wchar_t));
            if (new_path) {
                _snwprintf_s(new_path, new_cap, _TRUNCATE, L"%ls;%ls", libr_dir, env_path);
                set_env_win(L"PATH", new_path);
                free(new_path);
            }
        }
        free(env_path);
    }

    set_env_win(L"_RCHITECT_LIBR_LOADED", L"1");
}

int wmain(int argc, wchar_t **argv) {
    wchar_t dll_path[32768];
    if (!GetEnvironmentVariableW(L"_RCHITECT_PYTHON_DLL", dll_path, 32768)) {
        fwprintf(stderr, L"_RCHITECT_PYTHON_DLL is not set\n");
        return 1;
    }
    GetEnvironmentVariableW(L"_RCHITECT_BASE_EXE", g_fake_base_exe, 32768);

    /* Clear internal bootstrap env vars so child processes do not inherit them */
    set_env_win(L"_RCHITECT_PYTHON_DLL", NULL);
    set_env_win(L"_RCHITECT_BASE_EXE", NULL);

    wchar_t rhome[32768];
    if (resolve_rhome_win(argc, argv, rhome, 32768)) {
        setup_r_dll_win(rhome);
    }

    wchar_t dll_dir[32768];
    if (!GetFullPathNameW(dll_path, 32768, dll_dir, NULL)) {
        wcscpy_s(dll_dir, 32768, dll_path);
    }
    wchar_t *last_bslash = wcsrchr(dll_dir, L'\\');
    wchar_t *last_fslash = wcsrchr(dll_dir, L'/');
    wchar_t *last_slash = (last_fslash > last_bslash) ? last_fslash : last_bslash;
    if (last_slash) {
        *last_slash = L'\0';
        AddDllDirectory(dll_dir);
    }

    HMODULE hPy = LoadLibraryExW(
        dll_path,
        NULL,
        LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR
    );
    if (!hPy) {
        fwprintf(stderr, L"Failed to load Python DLL: %ls (error %lu)\n", dll_path, GetLastError());
        return 1;
    }

    patch_iat_getmodulefilenamew(hPy);

    Py_Main_t py_main = (Py_Main_t)GetProcAddress(hPy, "Py_Main");
    if (!py_main) {
        fwprintf(stderr, L"Failed to locate Py_Main in %ls\n", dll_path);
        return 1;
    }

    if (g_fake_base_exe[0] != L'\0') {
        argv[0] = g_fake_base_exe;
    }

    return py_main(argc, argv);
}
