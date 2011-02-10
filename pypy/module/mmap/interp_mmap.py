from pypy.rpython.tool import rffi_platform
from pypy.rpython.lltypesystem import rffi, lltype
from pypy.interpreter.error import OperationError, wrap_oserror
from pypy.interpreter.baseobjspace import W_Root, ObjSpace, Wrappable
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app, NoneNotWrapped
from pypy.rlib import rmmap
from pypy.rlib.rmmap import RValueError, RTypeError, ROverflowError
import sys
import os
import platform
import stat

class W_MMap(Wrappable):
    def __init__(self, space, mmap_obj):
        self.space = space
        self.mmap = mmap_obj
        
    def close(self):
        self.mmap.close()
    close.unwrap_spec = ['self']

    def read_byte(self):
        try:
            return self.space.wrap(self.mmap.read_byte())
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
    read_byte.unwrap_spec = ['self']
    
    def readline(self):
        return self.space.wrap(self.mmap.readline())
    readline.unwrap_spec = ['self']
    
    def read(self, num=-1):
        self.check_valid()
        return self.space.wrap(self.mmap.read(num))
    read.unwrap_spec = ['self', int]

    def find(self, tofind, w_start=NoneNotWrapped, w_end=NoneNotWrapped):
        space = self.space
        if w_start is None:
            start = self.mmap.pos
        else:
            start = space.getindex_w(w_start, None)
        if w_end is None:
            end = self.mmap.size
        else:
            end = space.getindex_w(w_end, None)
        return space.wrap(self.mmap.find(tofind, start, end))
    find.unwrap_spec = ['self', 'bufferstr', W_Root, W_Root]

    def rfind(self, tofind, w_start=NoneNotWrapped, w_end=NoneNotWrapped):
        space = self.space
        if w_start is None:
            start = self.mmap.pos
        else:
            start = space.getindex_w(w_start, None)
        if w_end is None:
            end = self.mmap.size
        else:
            end = space.getindex_w(w_end, None)
        return space.wrap(self.mmap.find(tofind, start, end, True))
    rfind.unwrap_spec = ['self', 'bufferstr', W_Root, W_Root]

    def seek(self, pos, whence=0):
        try:
            self.mmap.seek(pos, whence)
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))            
    seek.unwrap_spec = ['self', 'index', int]
    
    def tell(self):
        return self.space.wrap(self.mmap.tell())
    tell.unwrap_spec = ['self']
    
    def descr_size(self):
        try:
            return self.space.wrap(self.mmap.file_size())
        except OSError, e:
            raise mmap_error(self.space, e)
    descr_size.unwrap_spec = ['self']
    
    def write(self, data):
        self.check_writeable()
        try:
            self.mmap.write(data)
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
    write.unwrap_spec = ['self', 'bufferstr']
    
    def write_byte(self, byte):
        try:
            self.mmap.write_byte(byte)
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
        except RTypeError, v:
            raise OperationError(self.space.w_TypeError,
                                 self.space.wrap(v.message))
    write_byte.unwrap_spec = ['self', str]

    def flush(self, offset=0, size=0):
        try:
            return self.space.wrap(self.mmap.flush(offset, size))
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
        except OSError, e:
            raise mmap_error(self.space, e)
    flush.unwrap_spec = ['self', int, int]
    
    def move(self, dest, src, count):
        try:
            self.mmap.move(dest, src, count)
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
    move.unwrap_spec = ['self', int, int, int]
    
    def resize(self, newsize):
        self.check_valid()
        self.check_resizeable()
        try:
            self.mmap.resize(newsize)
        except OSError, e:
            raise mmap_error(self.space, e)
    resize.unwrap_spec = ['self', int]
    
    def __len__(self):
        return self.space.wrap(self.mmap.size)
    __len__.unwrap_spec = ['self']

    def check_valid(self):
        try:
            self.mmap.check_valid()
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))

    def check_writeable(self):
        try:
            self.mmap.check_writeable()
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
        except RTypeError, v:
            raise OperationError(self.space.w_TypeError,
                                 self.space.wrap(v.message))

    def check_resizeable(self):
        try:
            self.mmap.check_resizeable()
        except RValueError, v:
            raise OperationError(self.space.w_ValueError,
                                 self.space.wrap(v.message))
        except RTypeError, v:
            raise OperationError(self.space.w_TypeError,
                                 self.space.wrap(v.message))

    def descr_getitem(self, w_index):
        self.check_valid()

        space = self.space
        start, stop, step = space.decode_index(w_index, self.mmap.size)
        if step == 0:  # index only
            return space.wrap(self.mmap.getitem(start))
        else:
            res = "".join([self.mmap.getitem(i)
                           for i in range(start, stop, step)])
            return space.wrap(res)
    descr_getitem.unwrap_spec = ['self', W_Root]

    def descr_setitem(self, w_index, w_value):
        space = self.space
        value = space.realstr_w(w_value)
        self.check_valid()

        self.check_writeable()

        start, stop, step, length = space.decode_index4(w_index, self.mmap.size)
        if step == 0:  # index only
            if len(value) != 1:
                raise OperationError(space.w_ValueError,
                                     space.wrap("mmap assignment must be "
                                                "single-character string"))
            self.mmap.setitem(start, value)
        else:
            if len(value) != length:
                raise OperationError(space.w_ValueError,
                          space.wrap("mmap slice assignment is wrong size"))
            for i in range(length):
                self.mmap.setitem(start, value[i])
                start += step
    descr_setitem.unwrap_spec = ['self', W_Root, W_Root]

    def descr_buffer(self):
        # XXX improve to work directly on the low-level address
        from pypy.interpreter.buffer import StringLikeBuffer
        space = self.space
        return space.wrap(StringLikeBuffer(space, space.wrap(self)))
    descr_buffer.unwrap_spec = ['self']

if rmmap._POSIX:

    def mmap(space, w_subtype, fileno, length, flags=rmmap.MAP_SHARED,
             prot=rmmap.PROT_WRITE | rmmap.PROT_READ,
             access=rmmap._ACCESS_DEFAULT, offset=0):
        self = space.allocate_instance(W_MMap, w_subtype)
        try:
            W_MMap.__init__(self, space,
                            rmmap.mmap(fileno, length, flags, prot, access,
                                       offset))
        except OSError, e:
            raise mmap_error(space, e)
        except RValueError, e:
            raise OperationError(space.w_ValueError, space.wrap(e.message))
        except RTypeError, e:
            raise OperationError(space.w_TypeError, space.wrap(e.message))
        except ROverflowError, e:
            raise OperationError(space.w_OverflowError, space.wrap(e.message))
        return space.wrap(self)
    mmap.unwrap_spec = [ObjSpace, W_Root, int, 'index', int, int, int, 'index']

elif rmmap._MS_WINDOWS:

    def mmap(space, w_subtype, fileno, length, tagname="",
             access=rmmap._ACCESS_DEFAULT, offset=0):
        self = space.allocate_instance(W_MMap, w_subtype)
        try:
            W_MMap.__init__(self, space,
                            rmmap.mmap(fileno, length, tagname, access,
                                       offset))
        except OSError, e:
            raise mmap_error(space, e)
        except RValueError, e:
            raise OperationError(space.w_ValueError, space.wrap(e.message))
        except RTypeError, e:
            raise OperationError(space.w_TypeError, space.wrap(e.message))
        except ROverflowError, e:
            raise OperationError(space.w_OverflowError, space.wrap(e.message))
        return space.wrap(self)
    mmap.unwrap_spec = [ObjSpace, W_Root, int, 'index', str, int, 'index']

W_MMap.typedef = TypeDef("mmap",
    __new__ = interp2app(mmap),
    close = interp2app(W_MMap.close),
    read_byte = interp2app(W_MMap.read_byte),
    readline = interp2app(W_MMap.readline),
    read = interp2app(W_MMap.read),
    find = interp2app(W_MMap.find),
    rfind = interp2app(W_MMap.rfind),
    seek = interp2app(W_MMap.seek),
    tell = interp2app(W_MMap.tell),
    size = interp2app(W_MMap.descr_size),
    write = interp2app(W_MMap.write),
    write_byte = interp2app(W_MMap.write_byte),
    flush = interp2app(W_MMap.flush),
    move = interp2app(W_MMap.move),
    resize = interp2app(W_MMap.resize),
    __module__ = "mmap",

    __len__ = interp2app(W_MMap.__len__),
    __getitem__ = interp2app(W_MMap.descr_getitem),
    __setitem__ = interp2app(W_MMap.descr_setitem),
    __buffer__ = interp2app(W_MMap.descr_buffer),
)

constants = rmmap.constants
PAGESIZE = rmmap.PAGESIZE
ALLOCATIONGRANULARITY = rmmap.ALLOCATIONGRANULARITY

def mmap_error(space, e):
    w_module = space.getbuiltinmodule('mmap')
    w_error = space.getattr(w_module, space.wrap('error'))
    return wrap_oserror(space, e, w_exception_class=w_error)
