import threading

class Counter:
    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0
