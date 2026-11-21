"""
Unit Tests for Thread-Safe Task Manager and Background Worker Execution
"""
import unittest
import time
from core.task_manager import TaskManager


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        TaskManager._instance = None
        self.tm = TaskManager(max_workers=2)

    def tearDown(self):
        self.tm.shutdown(wait=True)
        TaskManager._instance = None

    def test_background_task_execution(self):
        """Verify task runs in background and places result in queue"""
        def _slow_add(a, b):
            time.sleep(0.05)
            return a + b

        res_holder = []
        err_holder = []

        def _on_success(res):
            res_holder.append(res)

        def _on_err(err):
            err_holder.append(err)

        task_id = self.tm.submit_task(
            _slow_add, 10, 25,
            on_success=_on_success,
            on_error=_on_err,
            task_name="Test Addition"
        )
        self.assertIsNotNone(task_id)

        # Wait for worker to finish and put in queue
        time.sleep(0.15)

        # Manually drain queue
        self.assertFalse(self.tm._result_queue.empty())
        item = self.tm._result_queue.get()
        self.assertTrue(item.success)
        self.assertEqual(item.result, 35)

        item.on_success(item.result)
        self.assertEqual(res_holder, [35])
        self.assertEqual(err_holder, [])

    def test_background_task_error_handling(self):
        """Verify errors in worker thread are captured and reported safely"""
        def _failing_task():
            raise ValueError("Simulated mathematical failure")

        err_holder = []

        def _on_err(err):
            err_holder.append(err)

        self.tm.submit_task(
            _failing_task,
            on_error=_on_err,
            task_name="Failing Task"
        )

        time.sleep(0.1)

        self.assertFalse(self.tm._result_queue.empty())
        item = self.tm._result_queue.get()
        self.assertFalse(item.success)
        self.assertIsInstance(item.error, ValueError)

        item.on_error(item.error)
        self.assertEqual(len(err_holder), 1)
        self.assertIn("Simulated mathematical failure", str(err_holder[0]))


if __name__ == "__main__":
    unittest.main()
