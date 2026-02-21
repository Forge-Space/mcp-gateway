#!/usr/bin/env python3
"""
Performance benchmarking script for serverless MCP sleep architecture.
Validates success metrics: wake time < 200ms, memory reduction > 60%, etc.
"""

import asyncio
import time
import statistics
import docker
import json
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add service_manager to path
sys.path.append(str(Path(__file__).parent.parent))

from service_manager import ServiceManager, GlobalSleepSettings, ResourceMonitor


@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    test_name: str
    wake_times_ms: List[float]
    sleep_times_ms: List[float]
    memory_baseline_mb: float
    memory_sleep_mb: float
    memory_reduction_percent: float
    success_rate: float
    error_count: int
    total_operations: int


class SleepWakeBenchmark:
    """Performance benchmarking for sleep/wake operations."""

    def __init__(self):
        self.docker_client = docker.from_env()
        self.results: List[BenchmarkResult] = []

    async def setup_test_service(self, service_name: str = "benchmark-service") -> Dict:
        """Set up a test service for benchmarking."""
        # Create a simple container that can be paused/unpaused
        container = self.docker_client.containers.run(
            "alpine:latest",
            command=["sh", "-c", "echo 'Benchmark service running' && sleep 3600"],
            name=service_name,
            detach=True,
            labels={"benchmark": "true", "service": service_name}
        )

        # Wait for container to be ready
        await asyncio.sleep(2)

        # Get baseline memory usage
        stats = container.stats(stream=False)
        baseline_memory_mb = stats["memory_stats"]["usage"] / (1024 * 1024)

        return {
            "container_id": container.id,
            "baseline_memory_mb": baseline_memory_mb,
            "container": container
        }

    async def cleanup_test_service(self, service_info: Dict):
        """Clean up test service."""
        try:
            container = service_info["container"]
            container.remove(force=True)
        except Exception as e:
            print(f"Warning: Failed to cleanup container: {e}")

    async def benchmark_wake_performance(self, service_info: Dict, iterations: int = 10) -> BenchmarkResult:
        """Benchmark wake performance with multiple iterations."""
        container = service_info["container"]
        wake_times = []
        sleep_times = []
        error_count = 0

        print(f"Running wake performance benchmark with {iterations} iterations...")

        for i in range(iterations):
            try:
                # Sleep the container
                sleep_start = time.time()
                container.pause()
                sleep_time = (time.time() - sleep_start) * 1000
                sleep_times.append(sleep_time)

                # Small delay to ensure pause is complete
                await asyncio.sleep(0.1)

                # Wake the container
                wake_start = time.time()
                container.unpause()
                wake_time = (time.time() - wake_start) * 1000
                wake_times.append(wake_time)

                # Small delay between operations
                await asyncio.sleep(0.1)

                print(f"  Iteration {i+1}: Wake time {wake_time:.2f}ms, Sleep time {sleep_time:.2f}ms")

            except Exception as e:
                error_count += 1
                print(f"  Iteration {i+1}: Error - {e}")

        # Get memory usage during sleep (last iteration)
        sleep_stats = container.stats(stream=False)
        sleep_memory_mb = sleep_stats["memory_stats"]["usage"] / (1024 * 1024)

        memory_reduction = ((service_info["baseline_memory_mb"] - sleep_memory_mb) /
                           service_info["baseline_memory_mb"]) * 100

        success_rate = ((iterations - error_count) / iterations) * 100

        return BenchmarkResult(
            test_name="Wake Performance",
            wake_times_ms=wake_times,
            sleep_times_ms=sleep_times,
            memory_baseline_mb=service_info["baseline_memory_mb"],
            memory_sleep_mb=sleep_memory_mb,
            memory_reduction_percent=memory_reduction,
            success_rate=success_rate,
            error_count=error_count,
            total_operations=iterations
        )

    async def benchmark_memory_efficiency(self, service_info: Dict) -> BenchmarkResult:
        """Benchmark memory efficiency during sleep."""
        container = service_info["container"]

        print("Running memory efficiency benchmark...")

        # Get baseline memory
        baseline_stats = container.stats(stream=False)
        baseline_memory = baseline_stats["memory_stats"]["usage"] / (1024 * 1024)

        # Sleep the container
        container.pause()
        await asyncio.sleep(1)  # Allow memory to stabilize

        # Get memory during sleep
        sleep_stats = container.stats(stream=False)
        sleep_memory = sleep_stats["memory_stats"]["usage"] / (1024 * 1024)

        # Wake the container
        container.unpause()
        await asyncio.sleep(1)

        # Get memory after wake
        wake_stats = container.stats(stream=False)
        wake_memory = wake_stats["memory_stats"]["usage"] / (1024 * 1024)

        memory_reduction = ((baseline_memory - sleep_memory) / baseline_memory) * 100
        memory_recovery = ((wake_memory - sleep_memory) / sleep_memory) * 100 if sleep_memory > 0 else 0

        print(f"  Baseline memory: {baseline_memory:.2f}MB")
        print(f"  Sleep memory: {sleep_memory:.2f}MB")
        print(f"  Wake memory: {wake_memory:.2f}MB")
        print(f"  Memory reduction: {memory_reduction:.2f}%")
        print(f"  Memory recovery: {memory_recovery:.2f}%")

        return BenchmarkResult(
            test_name="Memory Efficiency",
            wake_times_ms=[],
            sleep_times_ms=[],
            memory_baseline_mb=baseline_memory,
            memory_sleep_mb=sleep_memory,
            memory_reduction_percent=memory_reduction,
            success_rate=100.0,
            error_count=0,
            total_operations=1
        )

    async def benchmark_concurrent_operations(self, service_info: Dict, concurrent_count: int = 5) -> BenchmarkResult:
        """Benchmark concurrent sleep/wake operations."""
        container = service_info["container"]

        print(f"Running concurrent operations benchmark with {concurrent_count} concurrent operations...")

        async def sleep_wake_cycle():
            """Single sleep/wake cycle."""
            try:
                sleep_start = time.time()
                container.pause()
                sleep_time = (time.time() - sleep_start) * 1000

                await asyncio.sleep(0.1)

                wake_start = time.time()
                container.unpause()
                wake_time = (time.time() - wake_start) * 1000

                return wake_time, sleep_time, None
            except Exception as e:
                return None, None, e

        # Run concurrent operations
        start_time = time.time()
        tasks = [sleep_wake_cycle() for _ in range(concurrent_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.time() - start_time) * 1000

        wake_times = []
        sleep_times = []
        error_count = 0

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            else:
                wake_time, sleep_time, error = result
                if error:
                    error_count += 1
                else:
                    wake_times.append(wake_time)
                    sleep_times.append(sleep_time)

        success_rate = ((concurrent_count - error_count) / concurrent_count) * 100

        print(f"  Total time: {total_time:.2f}ms for {concurrent_count} operations")
        print(f"  Average per operation: {total_time/concurrent_count:.2f}ms")
        print(f"  Success rate: {success_rate:.2f}%")

        return BenchmarkResult(
            test_name="Concurrent Operations",
            wake_times_ms=wake_times,
            sleep_times_ms=sleep_times,
            memory_baseline_mb=service_info["baseline_memory_mb"],
            memory_sleep_mb=0,
            memory_reduction_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            total_operations=concurrent_count
        )

    def analyze_results(self, results: List[BenchmarkResult]) -> Dict:
        """Analyze benchmark results against success criteria."""
        analysis = {
            "overall_success": True,
            "criteria_met": {},
            "performance_summary": {},
            "recommendations": []
        }

        for result in results:
            test_analysis = {
                "success": True,
                "issues": []
            }

            if result.test_name == "Wake Performance":
                # Check wake time target: < 200ms for 90% of operations
                if result.wake_times_ms:
                    wake_p95 = statistics.quantiles(result.wake_times_ms, n=20)[18]  # 95th percentile
                    wake_avg = statistics.mean(result.wake_times_ms)
                    wake_max = max(result.wake_times_ms)

                    test_analysis["wake_performance"] = {
                        "avg_ms": wake_avg,
                        "p95_ms": wake_p95,
                        "max_ms": wake_max,
                        "target_met": wake_p95 < 200
                    }

                    if wake_p95 >= 200:
                        test_analysis["success"] = False
                        test_analysis["issues"].append(f"Wake time P95 {wake_p95:.2f}ms exceeds 200ms target")

                    analysis["performance_summary"]["wake_times"] = test_analysis["wake_performance"]

                # Check success rate target: > 99.9%
                if result.success_rate < 99.9:
                    test_analysis["success"] = False
                    test_analysis["issues"].append(f"Success rate {result.success_rate:.2f}% below 99.9% target")

                test_analysis["success_rate"] = result.success_rate

            elif result.test_name == "Memory Efficiency":
                # Check memory reduction target: > 60%
                memory_reduction_met = result.memory_reduction_percent > 60
                test_analysis["memory_efficiency"] = {
                    "baseline_mb": result.memory_baseline_mb,
                    "sleep_mb": result.memory_sleep_mb,
                    "reduction_percent": result.memory_reduction_percent,
                    "target_met": memory_reduction_met
                }

                if not memory_reduction_met:
                    test_analysis["success"] = False
                    test_analysis["issues"].append(f"Memory reduction {result.memory_reduction_percent:.2f}% below 60% target")

                analysis["performance_summary"]["memory_efficiency"] = test_analysis["memory_efficiency"]

            elif result.test_name == "Concurrent Operations":
                # Check concurrent operation performance
                if result.wake_times_ms:
                    avg_wake_time = statistics.mean(result.wake_times_ms)
                    test_analysis["concurrent_performance"] = {
                        "avg_wake_time_ms": avg_wake_time,
                        "success_rate": result.success_rate,
                        "target_met": result.success_rate > 95 and avg_wake_time < 500
                    }

                    if result.success_rate < 95:
                        test_analysis["success"] = False
                        test_analysis["issues"].append(f"Concurrent success rate {result.success_rate:.2f}% below 95% target")

                analysis["performance_summary"]["concurrent_operations"] = test_analysis.get("concurrent_performance", {})

            analysis["criteria_met"][result.test_name] = test_analysis

            if not test_analysis["success"]:
                analysis["overall_success"] = False

        # Generate recommendations
        if not analysis["overall_success"]:
            analysis["recommendations"].append("Some performance targets were not met. Consider optimization.")

        wake_perf = analysis["performance_summary"].get("wake_times", {})
        if wake_perf.get("avg_ms", 0) > 100:
            analysis["recommendations"].append("Consider optimizing wake performance for better user experience.")

        memory_eff = analysis["performance_summary"].get("memory_efficiency", {})
        if memory_eff.get("reduction_percent", 0) < 50:
            analysis["recommendations"].append("Memory optimization could be improved for better resource efficiency.")

        return analysis

    def print_results(self, results: List[BenchmarkResult], analysis: Dict):
        """Print benchmark results in a formatted way."""
        print("\n" + "="*60)
        print("SERVERLESS MCP SLEEP ARCHITECTURE BENCHMARK RESULTS")
        print("="*60)

        for result in results:
            print(f"\n{result.test_name}:")
            print("-" * len(result.test_name))

            if result.wake_times_ms:
                wake_avg = statistics.mean(result.wake_times_ms)
                wake_p95 = statistics.quantiles(result.wake_times_ms, n=20)[18] if len(result.wake_times_ms) > 20 else max(result.wake_times_ms)
                wake_max = max(result.wake_times_ms)
                print(f"  Wake Times: Avg={wake_avg:.2f}ms, P95={wake_p95:.2f}ms, Max={wake_max:.2f}ms")

            if result.sleep_times_ms:
                sleep_avg = statistics.mean(result.sleep_times_ms)
                sleep_max = max(result.sleep_times_ms)
                print(f"  Sleep Times: Avg={sleep_avg:.2f}ms, Max={sleep_max:.2f}ms")

            if result.memory_reduction_percent > 0:
                print(f"  Memory: {result.memory_baseline_mb:.2f}MB → {result.memory_sleep_mb:.2f}MB ({result.memory_reduction_percent:.2f}% reduction)")

            print(f"  Success Rate: {result.success_rate:.2f}% ({result.total_operations - result.error_count}/{result.total_operations})")
            print(f"  Errors: {result.error_count}")

        print(f"\nOVERALL STATUS: {'✅ PASS' if analysis['overall_success'] else '❌ FAIL'}")

        if not analysis['overall_success']:
            print("\nIssues Found:")
            for test_name, criteria in analysis['criteria_met'].items():
                if not criteria['success']:
                    for issue in criteria['issues']:
                        print(f"  • {issue}")

        if analysis['recommendations']:
            print("\nRecommendations:")
            for rec in analysis['recommendations']:
                print(f"  • {rec}")

        print("\nSuccess Criteria Validation:")
        print("  • Wake time < 200ms for 90% of services: " +
              ("✅" if analysis['performance_summary'].get('wake_times', {}).get('target_met', False) else "❌"))
        print("  • Memory reduction > 60% for sleeping services: " +
              ("✅" if analysis['performance_summary'].get('memory_efficiency', {}).get('target_met', False) else "❌"))
        print("  • 99.9% successful sleep/wake operations: " +
              ("✅" if any(criteria.get('success_rate', 0) >= 99.9 for criteria in analysis['criteria_met'].values()) else "❌"))

        print("\n" + "="*60)

    async def run_full_benchmark(self):
        """Run the complete benchmark suite."""
        print("Starting Serverless MCP Sleep Architecture Benchmark...")
        print("This will test real Docker containers with pause/unpause operations.")

        service_info = None
        try:
            # Set up test service
            service_info = await self.setup_test_service()

            # Run benchmarks
            results = []

            # Wake performance benchmark
            wake_result = await self.benchmark_wake_performance(service_info, iterations=10)
            results.append(wake_result)

            # Memory efficiency benchmark
            memory_result = await self.benchmark_memory_efficiency(service_info)
            results.append(memory_result)

            # Concurrent operations benchmark
            concurrent_result = await self.benchmark_concurrent_operations(service_info, concurrent_count=5)
            results.append(concurrent_result)

            # Analyze results
            analysis = self.analyze_results(results)

            # Print results
            self.print_results(results, analysis)

            # Save results to file
            self.save_results(results, analysis)

            return analysis['overall_success']

        except Exception as e:
            print(f"Benchmark failed: {e}")
            return False
        finally:
            if service_info:
                await self.cleanup_test_service(service_info)

    def save_results(self, results: List[BenchmarkResult], analysis: Dict):
        """Save benchmark results to JSON file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "results": [
                {
                    "test_name": r.test_name,
                    "wake_times_ms": r.wake_times_ms,
                    "sleep_times_ms": r.sleep_times_ms,
                    "memory_baseline_mb": r.memory_baseline_mb,
                    "memory_sleep_mb": r.memory_sleep_mb,
                    "memory_reduction_percent": r.memory_reduction_percent,
                    "success_rate": r.success_rate,
                    "error_count": r.error_count,
                    "total_operations": r.total_operations
                }
                for r in results
            ],
            "analysis": analysis
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults saved to: {filename}")


async def main():
    """Main benchmark execution."""
    benchmark = SleepWakeBenchmark()

    try:
        success = await benchmark.run_full_benchmark()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Benchmark error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
