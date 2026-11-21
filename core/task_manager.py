"""
M4DI~UciH4 Trading Intelligence System
Thread-Safe Background Task Manager with Tkinter Main-Thread Dispatcher
"""
import queue
import threading
import uuid
from typing import Callable, Optional, Any, Dict
from concurrent.futures import ThreadPoolExecutor

from core.logger import get_app_logger

logger = get_app_logger("TaskManager")


class TaskResult:
    """Encapsulates execution result from background worker"""
    def __init__(self, task_id: str, name: str, success: bool, result: Any = None, error: Optional[Exception] = None,
                 on_success: Optional[Callable] = None, on_error: Optional[Callable] = None):
        self.task_id = task_id
        self.name = name
        self.success = success
        self.result = result
        self.error = error
        self.on_success = on_success
        self.on_error = on_error


class TaskManager:
    """
    Thread-Safe Task Manager for Asynchronous Background Execution.
    Ensures GUI never freezes by offloading work to threads and
    delivering callbacks safely to the Tkinter main thread via queue.Queue.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, max_workers: int = 4):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance._max_workers = max_workers
                cls._instance._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="M4DI_Worker")
                cls._instance._result_queue = queue.Queue()
                cls._instance._active_tasks: Dict[str, str] = {}
                cls._instance._active_lock = threading.Lock()
                cls._instance._is_running = True
            return cls._instance

    def submit_task(
        self,
        task_fn: Any,
        *args,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        task_name: str = "Background Task",
        **kwargs
    ) -> str:
        """
        Submit a heavy function to run in a background worker thread.
        on_success and on_error will be executed safely in the Tkinter main loop.
        """
        # Support swapped signature submit_task(name, fn)
        if isinstance(task_fn, str) and args and callable(args[0]):
            task_name = task_fn
            task_fn = args[0]
            args = args[1:]

        # Support on_complete alias
        if on_success is None and "on_complete" in kwargs:
            on_success = kwargs["on_complete"]

        task_id = str(uuid.uuid4())[:8]

        with self._active_lock:
            self._active_tasks[task_id] = task_name

        def _worker():
            try:
                res = task_fn(*args)
                item = TaskResult(
                    task_id=task_id,
                    name=task_name,
                    success=True,
                    result=res,
                    on_success=on_success,
                    on_error=on_error
                )
            except Exception as exc:
                logger.error(f"Task '{task_name}' [{task_id}] failed: {exc}")
                item = TaskResult(
                    task_id=task_id,
                    name=task_name,
                    success=False,
                    error=exc,
                    on_success=on_success,
                    on_error=on_error
                )
            finally:
                with self._active_lock:
                    self._active_tasks.pop(task_id, None)
                self._result_queue.put(item)

        self._executor.submit(_worker)
        return task_id

    def active_tasks_count(self) -> int:
        """Return current number of actively executing background tasks"""
        with self._active_lock:
            return len(self._active_tasks)

    def get_active_tasks_names(self) -> list[str]:
        """Return list of active task names"""
        with self._active_lock:
            return list(self._active_tasks.values())

    def start_polling(self, tk_root, interval_ms: int = 50):
        """
        Start periodic polling on the Tkinter main thread to process results
        from the result queue without blocking.
        """
        def _poll():
            if not self._is_running:
                return

            while not self._result_queue.empty():
                try:
                    item: TaskResult = self._result_queue.get_nowait()
                    if item.success:
                        if item.on_success:
                            try:
                                item.on_success(item.result)
                            except Exception as e:
                                logger.error(f"Error in on_success callback for task '{item.name}': {e}")
                    else:
                        if item.on_error:
                            try:
                                item.on_error(item.error)
                            except Exception as e:
                                logger.error(f"Error in on_error callback for task '{item.name}': {e}")
                    self._result_queue.task_done()
                except queue.Empty:
                    break

            try:
                if self._is_running and tk_root.winfo_exists():
                    tk_root.after(interval_ms, _poll)
            except Exception:
                pass

        tk_root.after(interval_ms, _poll)

    def shutdown(self, wait: bool = False):
        """Cleanly shutdown thread pool workers"""
        self._is_running = False
        try:
            self._executor.shutdown(wait=wait, cancel_futures=True)
        except Exception:
            pass
        with TaskManager._lock:
            TaskManager._instance = None
