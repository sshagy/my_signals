import signal, os, time

class Timeout:
    """
    Usage:
        1) context manager

        try:
            with Timeout(5):
                time.sleep(5)
        except Timeout.TimeoutException:
            pass
            
        or (work in progress)
        
        with Timeout(5):
            time.sleep(5)

        2) decorator

        @Timeout(5)
        def foo(n=10):
            time.sleep(n)

        foo()

        # TODO: support async_enter, async_exit, async_call
    """
    class TimeoutException(Exception):
        pass
    def __init__(self, sec: int, on_rise = None):
        self.timer_sec = sec
    def handler_alarm(self, signum, frame):
        # TODO: print -> log.debug
        # print(f'Signal handler called with signal {signum}.')
        raise self.TimeoutException(f'Alarm! Pass {self.timer_sec} sec.')
    def __enter__(self):
        # See https://ru.wikipedia.org/wiki/%D0%A1%D0%B8%D0%B3%D0%BD%D0%B0%D0%BB_(Unix)
        # See other signals: http://john16blog.blogspot.com/2013/02/python-signal.html
        # https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
        signal.signal(signal.SIGALRM, self.handler_alarm)
        signal.alarm(self.timer_sec)
        print(f'  Run alarm on {self.timer_sec} sec')
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is self.TimeoutException:
            print(f'  Timeout result: Slowpoke! {exc_val}')
        else:
            signal.alarm(0)
            print('  Timeout result: Good job!')
    def __call__(self, func):
        def wrapped(*args, **kwargs):
            try:
                with self:
                    return func(*args, **kwargs)
            except Timeout.TimeoutException:
                pass
        return wrapped

# t1 = time.perf_counter()
# try:
#     with Timeout(5):
#         print(1)
#         time.sleep(5)
#         print(2)
# except Timeout.TimeoutException:
#     pass
# print('Result:', time.perf_counter() - t1)

@Timeout(5)
def foo(n=10):
    time.sleep(n)
    return 'Ok!'

print(foo())
print(foo(4))
