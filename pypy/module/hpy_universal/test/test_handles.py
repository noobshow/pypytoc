from pypy.module.hpy_universal import handles
from pypy.module.hpy_universal.handles import HandleManager

class TestHandleManager(object):

    def test_new(self):
        mgr = HandleManager(None)
        h = mgr.new('hello')
        assert mgr.handles_w[h] == 'hello'

    def test_close(self):
        mgr = HandleManager(None)
        h = mgr.new('hello')
        assert mgr.close(h) is None
        assert mgr.handles_w[h] is None

    def test_consume(self):
        mgr = HandleManager(None)
        h = mgr.new('hello')
        assert mgr.consume(h) == 'hello'
        assert mgr.handles_w[h] is None

    def test_freelist(self):
        mgr = HandleManager(None)
        h0 = mgr.new('hello')
        h1 = mgr.new('world')
        assert mgr.consume(h0) == 'hello'
        assert mgr.free_list == [h0]
        h2 = mgr.new('hello2')
        assert h2 == h0
        assert mgr.free_list == []

    def test_dup(self):
        mgr = HandleManager(None)
        h0 = mgr.new('hello')
        h1 = mgr.dup(h0)
        assert h1 != h0
        assert mgr.consume(h0) == mgr.consume(h1) == 'hello'

def test_using():
    mgr = HandleManager(None)
    class FakeSpace(object):
        @classmethod
        def fromcache(cls, x):
            return mgr
    space = FakeSpace()
    with handles.using(space, 'hello') as h:
        assert mgr.handles_w[h] == 'hello'
    assert mgr.handles_w[h] is None