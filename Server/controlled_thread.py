from threading import Thread
import threading
import time
class ControlledThread:
    active_threads = {}
    # active_threads_count = 0
    _being_used = False
    max_threads = 9
    def __init__(self, target, args:tuple = (), name:str=None, wait_time = 3):
        starting_time = time.time()

        while threading.active_count() >= ControlledThread.max_threads or ControlledThread._being_used:
            time.sleep(0.1)
            if time.time() - starting_time > wait_time:
                print(f"El tiempo de espera para el hilo {name if name else threading.active_count()} sobrepaso lo esperado")
                return
        ControlledThread._being_used = True
        name = name if name else f"thread #{threading.active_count()}"
        ControlledThread.active_threads[name] = self
        # ControlledThread.active_threads_count += 1
        ControlledThread._being_used = False
        self.thread = Thread(target=self._start_controlled_thread, args=(target, args, name), daemon=True)
        self.thread.start()
    def _start_controlled_thread(self, method, args, name):
        try:
            method(*args)
        except Exception as e:
            print(f"Hubo un error no controlado en el ControlledThread:    [{e}]")
        finally:
            del ControlledThread.active_threads[name]
            # ControlledThread.active_threads_count -=1


