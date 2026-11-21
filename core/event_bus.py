"""
M4DI~UciH4 Trading Intelligence System
Thread-Safe Event Bus for Decoupled Messaging
"""
import threading
from typing import Callable, Dict, List, Any


class EventBus:
    """Thread-safe Pub/Sub Event Dispatcher"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers: Dict[str, List[Callable]] = {}
                cls._instance._sub_lock = threading.Lock()
            return cls._instance

    def subscribe(self, event_name: str, callback: Callable[[Any], None]):
        """Register a callback listener for an event"""
        with self._sub_lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            if callback not in self._subscribers[event_name]:
                self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Any], None]):
        """Remove a callback listener from an event"""
        with self._sub_lock:
            if event_name in self._subscribers and callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def emit(self, event_name: str, data: Any = None):
        """Emit an event to all registered listeners"""
        with self._sub_lock:
            callbacks = list(self._subscribers.get(event_name, []))
            
        for cb in callbacks:
            try:
                cb(data)
            except Exception as e:
                # Listener exception should not crash the event bus
                pass

    def clear(self):
        """Clear all subscribers"""
        with self._sub_lock:
            self._subscribers.clear()
