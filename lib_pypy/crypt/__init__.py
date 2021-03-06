"""
CFFI based implementation of the crypt module
"""

import sys
import cffi

ffi = cffi.FFI()
ffi.cdef('char *crypt(char *word, char *salt);')

try:
    lib = ffi.dlopen('crypt')
except OSError:
    raise ImportError('crypt not available')


def crypt(word, salt):
    res = lib.crypt(word, salt)
    if not res:
        return None
    return ffi.string(res)
