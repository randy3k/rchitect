#include <windows.h>
#include <stdio.h>
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

int wmain(int argc, wchar_t **argv) {
    wchar_t dll_path[32768];
    if (!GetEnvironmentVariableW(L"_RCHITECT_PYTHON_DLL", dll_path, 32768)) {
        fwprintf(stderr, L"_RCHITECT_PYTHON_DLL is not set\n");
        return 1;
    }
    GetEnvironmentVariableW(L"_RCHITECT_BASE_EXE", g_fake_base_exe, 32768);

    /* Clear internal bootstrap env vars so child processes do not inherit them */
    SetEnvironmentVariableW(L"_RCHITECT_PYTHON_DLL", NULL);
    SetEnvironmentVariableW(L"_RCHITECT_BASE_EXE", NULL);

    wchar_t dll_dir[32768];
    wcscpy_s(dll_dir, 32768, dll_path);
    wchar_t *last_slash = wcsrchr(dll_dir, L'\\');
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
