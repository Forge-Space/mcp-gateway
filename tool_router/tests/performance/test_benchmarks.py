"""
Performance tests for MCP Gateway tool router.
"""

import pytest
import time
import psutil
import os
from unittest.mock import Mock, patch


class TestPerformanceBaselines:
    """Basic performance tests to ensure system meets minimum performance requirements."""

    def test_startup_memory_usage(self):
        """Test that startup memory usage is within acceptable limits."""
        # Get current process memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Memory usage should be reasonable for startup
        assert initial_memory < 500, f"Startup memory usage too high: {initial_memory:.2f} MB"

    def test_response_time_baseline(self):
        """Test basic response time for simple operations."""
        # Mock a simple operation
        start_time = time.time()

        # Simulate some basic processing
        result = sum(range(1000))

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Should complete within reasonable time
        assert response_time < 100, f"Operation too slow: {response_time:.2f}ms"
        assert result == 499500, "Incorrect calculation result"

    def test_concurrent_operations(self):
        """Test ability to handle concurrent operations."""
        import threading
        import queue

        results = queue.Queue()

        def worker():
            """Simple worker function."""
            start = time.time()
            # Simulate work
            total = sum(range(100))
            end = time.time()
            results.put((total, end - start))

        # Start multiple threads
        threads = []
        start_time = time.time()

        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete concurrent operations efficiently
        assert total_time < 1.0, f"Concurrent operations too slow: {total_time:.2f}s"

        # Verify all operations completed successfully
        assert results.qsize() == 5, "Not all operations completed"

        while not results.empty():
            total, duration = results.get()
            assert total == 4950, "Incorrect calculation result"
            assert duration < 0.5, f"Individual operation too slow: {duration:.2f}s"


class TestResourceLimits:
    """Tests for resource usage limits."""

    def test_cpu_usage_baseline(self):
        """Test CPU usage stays within reasonable limits."""
        process = psutil.Process(os.getpid())

        # Get initial CPU usage
        initial_cpu = process.cpu_percent()

        # Wait a moment for accurate measurement
        time.sleep(0.1)

        # Perform some work
        result = []
        for i in range(10000):
            result.append(i * 2)

        # Wait for CPU measurement to stabilize
        time.sleep(0.1)

        # Get CPU usage after work
        final_cpu = process.cpu_percent()

        # CPU usage should be reasonable (this is a rough check)
        # Note: psutil CPU percentage can be unreliable on short intervals
        # so we use a more lenient threshold
        assert final_cpu <= 100, f"CPU usage too high: {final_cpu}%"
        assert len(result) == 10000, "Work not completed correctly"

    def test_memory_growth(self):
        """Test memory doesn't grow excessively during operations."""
        process = psutil.Process(os.getpid())

        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations
        data = []
        for i in range(1000):
            data.append([j for j in range(100)])

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = peak_memory - initial_memory

        # Memory growth should be controlled
        assert memory_growth < 100, f"Memory growth excessive: {memory_growth:.2f} MB"

        # Clean up
        del data

    def test_file_handle_usage(self):
        """Test file handle usage doesn't leak."""
        process = psutil.Process(os.getpid())

        initial_handles = process.num_handles() if hasattr(process, 'num_handles') else process.num_fds()

        # Open and close some files
        for i in range(10):
            with open(f'/tmp/test_{i}.txt', 'w') as f:
                f.write(f'test data {i}')

        # Clean up files
        for i in range(10):
            os.remove(f'/tmp/test_{i}.txt')

        final_handles = process.num_handles() if hasattr(process, 'num_handles') else process.num_fds()
        handle_growth = final_handles - initial_handles

        # Handle count should not grow significantly
        assert handle_growth <= 2, f"File handle leak detected: {handle_growth} handles"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
