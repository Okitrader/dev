#!/usr/bin/env python3
"""
Concurrent Load Testing for Deep Research System
Tests the system with multiple concurrent requests directly
"""

import asyncio
import time
import random
import statistics
from typing import List, Dict, Any
import json
from datetime import datetime
import os

# Import the adapter directly
from research_manager_adapter import ResearchManagerAdapter

# Test configuration
CONCURRENT_USERS = [5, 10, 20, 50]  # Test with different user counts
QUERIES_PER_USER = 3
USE_NEW_ARCHITECTURE = os.getenv("TEST_NEW_ARCHITECTURE", "false").lower() == "true"

# Sample queries
SAMPLE_QUERIES = [
    "What are the latest developments in quantum computing?",
    "Explain the impact of AI on healthcare",
    "Compare renewable energy sources",
    "Best practices for microservices architecture",
    "Current state of electric vehicle adoption",
    "How blockchain works in supply chain",
    "Environmental impacts of cryptocurrency",
    "Machine learning algorithms explained",
    "Cybersecurity trends in 2024",
    "How neural networks process language",
    "Future of autonomous vehicles",
    "Climate change mitigation strategies",
    "5G technology applications",
    "Gene editing advancements",
    "Space exploration updates"
]

class LoadTestResults:
    """Stores and analyzes load test results"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        
    def add_result(self, user_count: int, query: str, success: bool, 
                   duration: float, error: str = None, quality_score: float = None):
        """Add a test result"""
        self.results.append({
            "timestamp": datetime.now().isoformat(),
            "user_count": user_count,
            "query": query,
            "success": success,
            "duration": duration,
            "error": error,
            "quality_score": quality_score
        })
    
    def analyze(self, user_count: int) -> Dict[str, Any]:
        """Analyze results for a specific user count"""
        user_results = [r for r in self.results if r["user_count"] == user_count]
        
        if not user_results:
            return {"error": "No results for user count"}
        
        successful = [r for r in user_results if r["success"]]
        failed = [r for r in user_results if not r["success"]]
        
        analysis = {
            "user_count": user_count,
            "total_requests": len(user_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(user_results) * 100,
            "error_types": {}
        }
        
        if successful:
            durations = [r["duration"] for r in successful]
            analysis["avg_duration"] = statistics.mean(durations)
            analysis["median_duration"] = statistics.median(durations)
            analysis["p95_duration"] = sorted(durations)[int(len(durations) * 0.95)]
            analysis["min_duration"] = min(durations)
            analysis["max_duration"] = max(durations)
            
            quality_scores = [r["quality_score"] for r in successful if r["quality_score"]]
            if quality_scores:
                analysis["avg_quality"] = statistics.mean(quality_scores)
        
        # Count error types
        for r in failed:
            error_type = r.get("error", "Unknown")[:50]
            analysis["error_types"][error_type] = analysis["error_types"].get(error_type, 0) + 1
        
        return analysis

async def run_single_query(adapter: ResearchManagerAdapter, query: str, 
                          user_id: int, results: LoadTestResults, user_count: int):
    """Run a single research query"""
    start_time = time.time()
    success = False
    error = None
    quality_score = None
    
    try:
        print(f"User {user_id} starting: {query[:50]}...")
        
        # Collect all output
        full_report = []
        async for update in adapter.run(query):
            full_report.append(update)
        
        # Extract quality score if available
        report_text = '\n'.join(full_report)
        if "Quality Score:" in report_text:
            try:
                score_line = [line for line in report_text.split('\n') if "Quality Score:" in line][0]
                quality_score = float(score_line.split(":")[-1].strip())
            except:
                pass
        
        success = True
        duration = time.time() - start_time
        print(f"User {user_id} completed in {duration:.2f}s")
        
    except Exception as e:
        error = str(e)
        duration = time.time() - start_time
        print(f"User {user_id} failed: {error}")
    
    results.add_result(user_count, query, success, duration, error, quality_score)

async def simulate_concurrent_users(user_count: int, results: LoadTestResults):
    """Simulate multiple concurrent users"""
    print(f"\n{'='*60}")
    print(f"Testing with {user_count} concurrent users")
    print(f"{'='*60}")
    
    # Create adapter instance
    adapter = ResearchManagerAdapter(use_new_architecture=USE_NEW_ARCHITECTURE)
    
    # Create tasks for all users
    tasks = []
    for user_id in range(user_count):
        # Each user runs multiple queries
        for query_num in range(QUERIES_PER_USER):
            query = random.choice(SAMPLE_QUERIES)
            # Add slight delay to simulate realistic user behavior
            delay = random.uniform(0, 2)
            task = asyncio.create_task(
                run_with_delay(delay, run_single_query(
                    adapter, query, user_id, results, user_count
                ))
            )
            tasks.append(task)
    
    # Wait for all tasks to complete
    start_time = time.time()
    await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"\nCompleted {user_count} users in {total_time:.2f}s")
    print(f"Throughput: {len(tasks)/total_time:.2f} requests/second")

async def run_with_delay(delay: float, coro):
    """Run coroutine after delay"""
    await asyncio.sleep(delay)
    return await coro

def generate_report(results: LoadTestResults):
    """Generate load test report"""
    print("\n" + "="*60)
    print("LOAD TEST REPORT")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Architecture: {'NEW' if USE_NEW_ARCHITECTURE else 'OLD'}")
    print(f"Total Requests: {len(results.results)}")
    
    for user_count in CONCURRENT_USERS:
        analysis = results.analyze(user_count)
        
        print(f"\n### {user_count} Concurrent Users ###")
        print(f"Success Rate: {analysis['success_rate']:.1f}%")
        
        if analysis.get('avg_duration'):
            print(f"Response Times:")
            print(f"  Average: {analysis['avg_duration']:.2f}s")
            print(f"  Median: {analysis['median_duration']:.2f}s")
            print(f"  95th Percentile: {analysis['p95_duration']:.2f}s")
            print(f"  Range: {analysis['min_duration']:.2f}s - {analysis['max_duration']:.2f}s")
        
        if analysis.get('avg_quality'):
            print(f"Average Quality Score: {analysis['avg_quality']:.2f}")
        
        if analysis['error_types']:
            print(f"Errors:")
            for error_type, count in analysis['error_types'].items():
                print(f"  {error_type}: {count}")
    
    # Save detailed results
    filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump({
            "config": {
                "architecture": "new" if USE_NEW_ARCHITECTURE else "old",
                "user_counts": CONCURRENT_USERS,
                "queries_per_user": QUERIES_PER_USER
            },
            "results": results.results,
            "analysis": {
                str(uc): results.analyze(uc) for uc in CONCURRENT_USERS
            }
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {filename}")

async def main():
    """Run the load test"""
    print("Deep Research System - Concurrent Load Test")
    print("="*60)
    
    results = LoadTestResults()
    
    # Test with increasing user counts
    for user_count in CONCURRENT_USERS:
        await simulate_concurrent_users(user_count, results)
        
        # Brief pause between tests
        if user_count != CONCURRENT_USERS[-1]:
            print("\nPausing before next test...")
            await asyncio.sleep(5)
    
    # Generate report
    generate_report(results)
    
    # Performance recommendations
    print("\n### Recommendations ###")
    
    # Check for performance degradation
    for i in range(1, len(CONCURRENT_USERS)):
        prev_analysis = results.analyze(CONCURRENT_USERS[i-1])
        curr_analysis = results.analyze(CONCURRENT_USERS[i])
        
        if prev_analysis.get('avg_duration') and curr_analysis.get('avg_duration'):
            degradation = (curr_analysis['avg_duration'] - prev_analysis['avg_duration']) / prev_analysis['avg_duration']
            if degradation > 0.5:  # 50% slower
                print(f"⚠️  Significant performance degradation at {CONCURRENT_USERS[i]} users")
                print(f"   Consider optimizing for concurrent requests")
    
    # Check error rates
    for user_count in CONCURRENT_USERS:
        analysis = results.analyze(user_count)
        if analysis['success_rate'] < 95:
            print(f"⚠️  High error rate at {user_count} users: {100-analysis['success_rate']:.1f}%")
            print(f"   Review error handling and retry logic")

if __name__ == "__main__":
    # Set up environment
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        exit(1)
    
    asyncio.run(main())