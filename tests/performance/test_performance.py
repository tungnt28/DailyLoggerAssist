"""
Performance Tests - Daily Logger Assist

Tests for application performance, load handling, and optimization validation.
"""

import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.work_item import WorkItem
from app.models.message import Message
from app.services.ai_service import AIService
from app.services.report_service import ReportService


class TestPerformance:
    """Test suite for performance benchmarks and optimization validation."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_api_response_times(self, client: TestClient, sample_user, authenticated_headers):
        """Test API response times for critical endpoints."""
        
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/v1/auth/me"),
            ("GET", "/api/v1/data/work-items"),
            ("GET", "/api/v1/reports/templates"),
        ]
        
        response_times = {}
        
        for method, endpoint in endpoints:
            start_time = time.time()
            
            if endpoint.startswith("/api/v1"):
                response = getattr(client, method.lower())(endpoint, headers=authenticated_headers)
            else:
                response = getattr(client, method.lower())(endpoint)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            response_times[endpoint] = response_time
            
            # Assert response time is under acceptable threshold
            assert response_time < 2.0, f"{endpoint} took {response_time:.2f}s (too slow)"
        
        # Print performance summary
        print("\nAPI Response Times:")
        for endpoint, time_taken in response_times.items():
            print(f"  {endpoint}: {time_taken:.3f}s")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_database_query_performance(self, db_session: Session, performance_work_items):
        """Test database query performance with large datasets."""
        
        # Test simple queries
        start_time = time.time()
        work_items = db_session.query(WorkItem).filter(
            WorkItem.user_id == performance_work_items[0].user_id
        ).all()
        simple_query_time = time.time() - start_time
        
        assert len(work_items) == 100
        assert simple_query_time < 1.0, f"Simple query took {simple_query_time:.2f}s"
        
        # Test complex queries with joins and filters
        start_time = time.time()
        filtered_items = db_session.query(WorkItem).filter(
            WorkItem.user_id == performance_work_items[0].user_id,
            WorkItem.confidence_score > 0.7,
            WorkItem.status == "completed"
        ).order_by(WorkItem.created_at.desc()).limit(50).all()
        complex_query_time = time.time() - start_time
        
        assert complex_query_time < 2.0, f"Complex query took {complex_query_time:.2f}s"
        
        # Test aggregation queries
        start_time = time.time()
        total_time = db_session.query(
            db_session.query(WorkItem.time_spent_minutes).filter(
                WorkItem.user_id == performance_work_items[0].user_id
            ).scalar_subquery()
        ).scalar()
        aggregation_time = time.time() - start_time
        
        assert aggregation_time < 1.0, f"Aggregation query took {aggregation_time:.2f}s"
        
        print(f"\nDatabase Query Performance:")
        print(f"  Simple query: {simple_query_time:.3f}s")
        print(f"  Complex query: {complex_query_time:.3f}s")
        print(f"  Aggregation: {aggregation_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_ai_service_performance(self, ai_service: AIService, performance_work_items):
        """Test AI service performance with batch processing."""
        
        # Test single item analysis
        single_start = time.time()
        single_result = await ai_service.analyze_content_with_context(
            "Fixed authentication bug in system",
            {"user_id": str(uuid4())}
        )
        single_time = time.time() - single_start
        
        assert single_time < 5.0, f"Single AI analysis took {single_time:.2f}s"
        
        # Test batch processing
        batch_start = time.time()
        batch_result = await ai_service.categorize_work_items(performance_work_items[:20])
        batch_time = time.time() - batch_start
        
        # Batch processing should be more efficient than individual calls
        expected_individual_time = single_time * 20
        efficiency_ratio = batch_time / expected_individual_time
        
        assert efficiency_ratio < 0.8, f"Batch processing not efficient enough: {efficiency_ratio:.2f}"
        
        print(f"\nAI Service Performance:")
        print(f"  Single analysis: {single_time:.3f}s")
        print(f"  Batch processing (20 items): {batch_time:.3f}s")
        print(f"  Efficiency ratio: {efficiency_ratio:.3f}")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_requests(self, client: TestClient, sample_user, authenticated_headers):
        """Test concurrent request handling."""
        
        def make_request():
            """Make a single API request."""
            start_time = time.time()
            response = client.get("/api/v1/data/work-items", headers=authenticated_headers)
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        results = {}
        
        for concurrency in concurrency_levels:
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrency)]
                responses = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            response_times = [response[1] for response in responses]
            success_count = sum(1 for response in responses if response[0] == 200)
            
            results[concurrency] = {
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "success_rate": success_count / concurrency,
                "throughput": concurrency / total_time
            }
            
            # Assertions for performance expectations
            assert results[concurrency]["success_rate"] >= 0.95, f"Low success rate at concurrency {concurrency}"
            assert results[concurrency]["avg_response_time"] < 5.0, f"High response time at concurrency {concurrency}"
        
        print("\nConcurrency Performance:")
        for concurrency, metrics in results.items():
            print(f"  {concurrency} concurrent requests:")
            print(f"    Avg response time: {metrics['avg_response_time']:.3f}s")
            print(f"    Max response time: {metrics['max_response_time']:.3f}s")
            print(f"    Success rate: {metrics['success_rate']:.1%}")
            print(f"    Throughput: {metrics['throughput']:.1f} req/s")

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_report_generation_performance(self, report_service: ReportService, 
                                                sample_user, performance_work_items):
        """Test report generation performance with large datasets."""
        
        # Daily report generation
        daily_start = time.time()
        daily_report = await report_service.generate_daily_report(
            str(sample_user.id),
            datetime.now().date(),
            "standard_daily"
        )
        daily_time = time.time() - daily_start
        
        assert daily_time < 10.0, f"Daily report generation took {daily_time:.2f}s"
        assert daily_report is not None
        
        # Weekly report generation
        weekly_start = time.time()
        weekly_report = await report_service.generate_weekly_report(
            str(sample_user.id),
            datetime.now().date() - timedelta(days=7),
            datetime.now().date(),
            "standard_weekly"
        )
        weekly_time = time.time() - weekly_start
        
        assert weekly_time < 30.0, f"Weekly report generation took {weekly_time:.2f}s"
        assert weekly_report is not None
        
        print(f"\nReport Generation Performance:")
        print(f"  Daily report: {daily_time:.3f}s")
        print(f"  Weekly report: {weekly_time:.3f}s")

    @pytest.mark.performance
    def test_memory_usage(self, client: TestClient, performance_work_items):
        """Test memory usage during heavy operations."""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory usage
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_dataset = []
        for i in range(1000):
            item_data = {
                "id": str(uuid4()),
                "description": f"Work item {i} " * 50,  # Large description
                "analysis": {"category": f"cat_{i}", "data": list(range(100))}
            }
            large_dataset.append(item_data)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        # Clean up
        del large_dataset
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_cleanup = peak_memory - final_memory
        
        print(f"\nMemory Usage:")
        print(f"  Baseline: {baseline_memory:.1f} MB")
        print(f"  Peak: {peak_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        print(f"  Cleanup: {memory_cleanup:.1f} MB")
        
        # Assert memory usage is reasonable
        assert memory_increase < 500, f"Memory increase too high: {memory_increase:.1f} MB"
        assert memory_cleanup > memory_increase * 0.8, "Poor memory cleanup"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_pagination_performance(self, client: TestClient, authenticated_headers, 
                                  db_session: Session, performance_work_items):
        """Test pagination performance with large datasets."""
        
        page_sizes = [10, 25, 50, 100]
        performance_metrics = {}
        
        for page_size in page_sizes:
            page_times = []
            
            # Test first few pages
            for page in range(1, 6):
                start_time = time.time()
                response = client.get(
                    f"/api/v1/data/work-items?page={page}&size={page_size}",
                    headers=authenticated_headers
                )
                end_time = time.time()
                page_times.append(end_time - start_time)
                
                assert response.status_code == 200
            
            performance_metrics[page_size] = {
                "avg_time": statistics.mean(page_times),
                "max_time": max(page_times),
                "min_time": min(page_times)
            }
            
            # Assert pagination performance
            assert performance_metrics[page_size]["avg_time"] < 2.0, \
                f"Pagination too slow for page size {page_size}"
        
        print("\nPagination Performance:")
        for size, metrics in performance_metrics.items():
            print(f"  Page size {size}:")
            print(f"    Avg time: {metrics['avg_time']:.3f}s")
            print(f"    Max time: {metrics['max_time']:.3f}s")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_background_task_performance(self, db_session: Session, sample_user, 
                                             performance_work_items):
        """Test background task processing performance."""
        
        from app.tasks.ai_processing import (
            process_messages_for_work_items,
            categorize_work_items,
            estimate_work_item_times
        )
        
        # Create test messages
        messages = []
        for i in range(50):
            message = Message(
                id=uuid4(),
                user_id=sample_user.id,
                source="teams",
                content=f"Completed task {i}, took about {30 + i % 60} minutes",
                sender="test@example.com",
                message_timestamp=datetime.utcnow() - timedelta(minutes=i),
                processed=False
            )
            messages.append(message)
        
        for message in messages:
            db_session.add(message)
        db_session.commit()
        
        # Test message processing
        start_time = time.time()
        result = await asyncio.get_event_loop().run_in_executor(
            None, process_messages_for_work_items, str(sample_user.id)
        )
        processing_time = time.time() - start_time
        
        assert processing_time < 30.0, f"Message processing took {processing_time:.2f}s"
        
        # Test work item categorization
        start_time = time.time()
        result = await asyncio.get_event_loop().run_in_executor(
            None, categorize_work_items, str(sample_user.id)
        )
        categorization_time = time.time() - start_time
        
        assert categorization_time < 20.0, f"Categorization took {categorization_time:.2f}s"
        
        print(f"\nBackground Task Performance:")
        print(f"  Message processing (50 items): {processing_time:.3f}s")
        print(f"  Work item categorization: {categorization_time:.3f}s")

    @pytest.mark.performance
    def test_cache_performance(self, client: TestClient, authenticated_headers):
        """Test caching effectiveness for repeated requests."""
        
        endpoint = "/api/v1/reports/templates"
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get(endpoint, headers=authenticated_headers)
        first_request_time = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time()
        response2 = client.get(endpoint, headers=authenticated_headers)
        second_request_time = time.time() - start_time
        
        # Third request (should still be cached)
        start_time = time.time()
        response3 = client.get(endpoint, headers=authenticated_headers)
        third_request_time = time.time() - start_time
        
        # All requests should return the same data
        assert response1.status_code == response2.status_code == response3.status_code
        assert response1.json() == response2.json() == response3.json()
        
        # Cached requests should be significantly faster
        cache_speedup = first_request_time / statistics.mean([second_request_time, third_request_time])
        
        print(f"\nCache Performance:")
        print(f"  First request (cache miss): {first_request_time:.3f}s")
        print(f"  Second request (cached): {second_request_time:.3f}s")
        print(f"  Third request (cached): {third_request_time:.3f}s")
        print(f"  Cache speedup: {cache_speedup:.1f}x")
        
        # Assert caching provides meaningful performance improvement
        # Note: This might not always be true for very fast endpoints
        if first_request_time > 0.1:  # Only test if first request takes significant time
            assert cache_speedup > 1.5, f"Cache not providing enough speedup: {cache_speedup:.1f}x"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_stress_test(self, client: TestClient, authenticated_headers):
        """Stress test the application with sustained load."""
        
        duration_seconds = 30  # 30-second stress test
        request_interval = 0.1  # 10 requests per second
        
        start_time = time.time()
        request_count = 0
        error_count = 0
        response_times = []
        
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            try:
                response = client.get("/health")
                request_end = time.time()
                
                response_times.append(request_end - request_start)
                request_count += 1
                
                if response.status_code != 200:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Request failed: {e}")
            
            # Control request rate
            elapsed = time.time() - request_start
            if elapsed < request_interval:
                time.sleep(request_interval - elapsed)
        
        total_time = time.time() - start_time
        error_rate = error_count / request_count if request_count > 0 else 1
        avg_response_time = statistics.mean(response_times) if response_times else 0
        throughput = request_count / total_time
        
        print(f"\nStress Test Results ({duration_seconds}s):")
        print(f"  Total requests: {request_count}")
        print(f"  Error rate: {error_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Throughput: {throughput:.1f} req/s")
        
        # Assert stress test performance
        assert error_rate < 0.05, f"High error rate during stress test: {error_rate:.1%}"
        assert avg_response_time < 2.0, f"High response time under stress: {avg_response_time:.3f}s"
        assert throughput > 5.0, f"Low throughput under stress: {throughput:.1f} req/s"

    @pytest.mark.performance
    def test_database_connection_pool(self, db_session: Session):
        """Test database connection pool performance."""
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def database_operation(thread_id):
            """Perform database operation in thread."""
            try:
                start_time = time.time()
                
                # Simulate database work
                result = db_session.execute("SELECT 1").scalar()
                
                end_time = time.time()
                results_queue.put({
                    'thread_id': thread_id,
                    'success': True,
                    'time': end_time - start_time,
                    'result': result
                })
            except Exception as e:
                results_queue.put({
                    'thread_id': thread_id,
                    'success': False,
                    'error': str(e),
                    'time': 0
                })
        
        # Test with multiple concurrent database connections
        num_threads = 10
        threads = []
        
        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=database_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        success_count = sum(1 for r in results if r['success'])
        avg_time = statistics.mean([r['time'] for r in results if r['success']])
        
        print(f"\nDatabase Connection Pool Test:")
        print(f"  Concurrent connections: {num_threads}")
        print(f"  Successful connections: {success_count}/{num_threads}")
        print(f"  Average operation time: {avg_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        
        assert success_count == num_threads, "Some database connections failed"
        assert avg_time < 1.0, f"Database operations too slow: {avg_time:.3f}s" 