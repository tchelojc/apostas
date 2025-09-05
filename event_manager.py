# project/event_manager.py
class EventManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._events = {}
        return cls._instance
    
    def subscribe(self, event_name, callback):
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(callback)
    
    def publish(self, event_name, data=None):
        for callback in self._events.get(event_name, []):
            callback(data)