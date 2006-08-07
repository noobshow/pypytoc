from ri386genop import *


def test_machinecodeblock():
    mc = MachineCodeBlock(4096)
    mc.MOV(eax, mem(esp, 4))
    mc.ADD(eax, mem(esp, 8))
    mc.RET()

    res = mc.execute(40, 2)
    assert res == 42
    return res

def test_compile():
    from pypy.translator.c.test.test_genc import compile

    fn = compile(test_machinecodeblock, [])
    res = fn()
    assert res == 42
