import signal, os, time, logging, asyncio, threading

logger = logging.getLogger(__name__)
# debug, warn = logger.debug, logger.warning
# debug, warn = print, print
debug, warn = logger.debug, logger.debug


class Timeout:
    """
    Usage:
        1) context manager:

        with Timeout(5):
            time.sleep(5)

        2) decorator:

        @Timeout(5)
        def foo(n):
            time.sleep(n)
            return 'Ok!'
        print(foo(10))

        3) async mode
        # TODO: support async_enter, async_exit, async_call
        
        4) Note: can't use signal with threading
    """

    class TimeoutException(Exception):
        pass

    def __init__(self, sec: int, is_rising: bool = False):
        self.timer_sec = sec
        self.is_rising = is_rising

    def handler_alarm(self, signum, frame):
        raise self.TimeoutException(f'Alarm! Pass {self.timer_sec} sec.')

    def __enter__(self):
        # See https://ru.wikipedia.org/wiki/%D0%A1%D0%B8%D0%B3%D0%BD%D0%B0%D0%BB_(Unix)
        # See other signals: http://john16blog.blogspot.com/2013/02/python-signal.html
        # https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
        signal.signal(signal.SIGALRM, self.handler_alarm)
        signal.alarm(self.timer_sec)
        debug(f'  Run alarm on {self.timer_sec} sec')
        # return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            signal.alarm(0)
            debug('  Timeout result: Good job!')
        elif exc_type is self.TimeoutException:
            warn(f'  Timeout result: Slowpoke! {exc_val}')
            return not self.is_rising

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            try:
                with self:
                    return func(*args, **kwargs)
            except Timeout.TimeoutException:
                if self.is_rising:
                    raise
        return wrapped

    async def __aenter__(self):
        self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

def test_cm():

    def foo(n):
        time.sleep(n)
        return 'Ok!'

    res = None
    with Timeout(1):
        res = foo(0.5)
    assert res == 'Ok!'
    print(1)

    res = None
    with Timeout(1):
        res = foo(2)
    assert res is None, res
    print(2)

    res = None
    try:
        with Timeout(1, is_rising=True):
            res = foo(2)
    except Timeout.TimeoutException:
        pass
    assert res is None, 3
    print(3)

    # Note: can't use signal in threads
    # ValueError: signal only works in main thread


def test_decorator():
    def foo(n):
        time.sleep(n)
        return 'Ok!'

    assert Timeout(1)(foo)(0.5) == 'Ok!'
    print(4)

    assert Timeout(1)(foo)(2) is None
    print(5)

    res = None
    try:
        res = Timeout(1, is_rising=True)(foo)(2)
    except Timeout.TimeoutException:
        pass
    assert res is None
    print(6)

def test_async():
    async def run():

        # @Timeout(1)
        async def foo(n):
            await asyncio.sleep(n)
            return 'Ok!'

        res = None
        async with Timeout(1):
            sleep_val = 2
            done, pending = await asyncio.wait([
                foo(sleep_val), foo(sleep_val), foo(sleep_val),
                foo(sleep_val), foo(sleep_val), foo(sleep_val),
                foo(sleep_val), foo(sleep_val), foo(sleep_val),
                foo(sleep_val), foo(sleep_val), foo(sleep_val),
                foo(sleep_val), foo(sleep_val), foo(sleep_val),
                foo(sleep_val), foo(sleep_val), foo(sleep_val),
            ], )
            res = [t.exception() or t.result() for t in done]
            res.extend([t.cancel() for t in pending])
        return res

    try:
        loop = asyncio.get_event_loop()
        r1 = loop.run_until_complete(run())
        print(4, r1)
    except Timeout.TimeoutException as e:
        print('err!', repr(e))


if __name__ == '__main__':
    test_cm()
    test_decorator()
    # test_async()
