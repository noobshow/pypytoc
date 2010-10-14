from pypy.rpython.lltypesystem import llmemory
from pypy.rlib.libffi import Func, types
from pypy.jit.metainterp.history import AbstractDescr
from pypy.jit.codewriter.effectinfo import EffectInfo
from pypy.jit.metainterp.test.test_optimizeopt import BaseTestOptimizeOpt, LLtypeMixin

class MyCallDescr(AbstractDescr):
    """
    Fake calldescr to be used inside the tests.

    The particularity is that it provides an __eq__ method, so that it
    comparses by value by comparing the arg_types and typeinfo fields, so you
    can check that the signature of a call is really what you want.
    """

    def __init__(self, arg_types, typeinfo):
        self.arg_types = arg_types
        self.typeinfo = typeinfo   # return type

    def __eq__(self, other):
        return self.arg_types == other.arg_types and self.typeinfo == other.typeinfo

class FakeLLObject(object):

    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        self._TYPE = llmemory.GCREF

    def _identityhash(self):
        return id(self)


class TestFfiCall(BaseTestOptimizeOpt, LLtypeMixin):

    class namespace:
        cpu = LLtypeMixin.cpu
        FUNC = LLtypeMixin.FUNC
        int_float__int = MyCallDescr('if', 'i')
        funcptr = FakeLLObject()
        func = FakeLLObject(_fake_class=Func,
                            argtypes=[types.sint, types.double],
                            restype=types.sint)
        #
        def calldescr(cpu, FUNC, oopspecindex):
            einfo = EffectInfo([], [], [], oopspecindex=oopspecindex)
            return cpu.calldescrof(FUNC, FUNC.ARGS, FUNC.RESULT, einfo)
        #
        libffi_prepare =  calldescr(cpu, FUNC, EffectInfo.OS_LIBFFI_PREPARE)
        libffi_push_arg = calldescr(cpu, FUNC, EffectInfo.OS_LIBFFI_PUSH_ARG)
        libffi_call =     calldescr(cpu, FUNC, EffectInfo.OS_LIBFFI_CALL)
    
    namespace = namespace.__dict__

    def test_ffi_call_opt(self):
        ops = """
        [i0, f1]
        call(0, ConstPtr(func),             descr=libffi_prepare)
        call(0, ConstPtr(func), i0,         descr=libffi_push_arg)
        call(0, ConstPtr(func), f1,         descr=libffi_push_arg)
        i3 = call(0, ConstPtr(func), 12345, descr=libffi_call)
        jump(i3, f1)
        """
        expected = """
        [i0, f1]
        i3 = call(12345, i0, f1, descr=int_float__int)
        jump(i3, f1)
        """
        loop = self.optimize_loop(ops, 'Not, Not', expected)

    def test_ffi_call_nonconst(self):
        ops = """
        [i0, f1, p2]
        call(0, p2,             descr=libffi_prepare)
        call(0, p2, i0,         descr=libffi_push_arg)
        call(0, p2, f1,         descr=libffi_push_arg)
        i3 = call(0, p2, 12345, descr=libffi_call)
        jump(i3, f1, p2)
        """
        expected = ops
        loop = self.optimize_loop(ops, 'Not, Not, Not', expected)

