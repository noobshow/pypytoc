import time
from rpython.rlib.rgil import yield_thread
from pypy.tool.pytest.objspace import gettestobjspace
from pypy.interpreter.gateway import interp2app
from pypy.module.thread.os_lock import allocate_lock
from pypy.module.thread.os_thread import start_new_thread
from pypy.module._multiprocessing.interp_semaphore import (
    create_semaphore, sem_unlink, W_SemLock)

def test_stuff(space):
    space = gettestobjspace(usemodules=['_multiprocessing', 'thread'])
    sem_name = '/test7'
    _handle = create_semaphore(space, sem_name, 1, 1)
    w_lock = W_SemLock(space, _handle, 0, 1)
    created = []
    successful = []
    N_THREADS = 16

    def run(space):
        w_sentinel = allocate_lock(space)
        yield_thread()
        w_sentinel.descr_lock_acquire(space)  # releases GIL
        yield_thread()
        created.append(w_sentinel)
        w_got = w_lock.acquire(space, w_timeout=space.newfloat(5.))  # releases GIL
        if space.is_true(w_got):
            yield_thread()
            w_lock.release(space)
            successful.append(w_sentinel)
        w_sentinel.descr_lock_release(space)
    w_run = space.wrap(interp2app(run))

    w_lock.acquire(space)
    for _ in range(N_THREADS):
        start_new_thread(space, w_run, space.newtuple([]))  # releases GIL
    deadline = time.time() + 5.
    while len(created) < N_THREADS:
        assert time.time() < deadline
        yield_thread()
    w_lock.release(space)

    for w_sentinel in created:
        # Join thread
        w_sentinel.descr_lock_acquire(space)  # releases GIL
        w_sentinel.descr_lock_release(space)
    assert len(successful) == N_THREADS