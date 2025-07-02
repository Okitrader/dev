#!/usr/bin/env python3
"""
Performance Regression Test Suite for Deep Research System
Automatically detects performance degradations between versions
"""

import asyncio
import json
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

from research_manager_adapter import ResearchManagerAdapter
from performance_optimizer import PerformanceRecord, PerformanceDimension

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASELINE_FILE = "performance_baseline.json"
RESULTS_DIR = "performance_test_results"
REGRESSION_THRESHOLD = 0.20  # 20% degradation triggers failure

# Test scenarios
@dataclass
class TestScenario:
    """Defines a performance test scenario"""
    name: str
    query: str
    expected_agents: List[str]
    performance_targets: Dict[str, float]  # dimension -> target value
    use_enhanced: bool = False
    cache_warmup: bool = False

# Standard test scenarios
TEST_SCENARIOS = [
    TestScenario(
        name="simple_query",
        query="What is machine learning?",
        expected_agents=["planner", "search", "writer"],
        performance_targets={
            "speed": 30.0,  # seconds
            "quality": 0.7,
            "cost": 1500  # tokens
        }
    ),
    TestScenario(
        name="complex_query",
        query="Compare the environmental impact of electric vehicles vs hydrogen fuel cell vehicles, including manufacturing, operation, and end-of-life considerations",
        expected_agents=["clarifier", "planner", "search", "writer"],
        performance_targets={
            "speed": 60.0,
            "quality": 0.8,
            "cost": 3000
        }
    ),
    TestScenario(
        name="enhanced_query",
        query="Analyze quantum computing breakthroughs in 2024\n\nReport Preferences: Format=Technical Deep-Dive, Audience=Technical Experts",
        expected_agents=["enhanced_planner", "enhanced_search", "enhanced_writer"],
        performance_targets={
            "speed": 90.0,
            "quality": 0.85,
            "cost": 4000
        },
        use_enhanced=True
    ),
    TestScenario(
        name="cached_query",
        query="What are the benefits of solar energy?",
        expected_agents=["planner", "search", "writer"],
        performance_targets={
            "speed": 15.0,  # Much faster with cache
            "quality": 0.7,
            "cost": 1500
        },
        cache_warmup=True
    )
]

@dataclass
class TestResult:
    """Stores results from a test run"""
    scenario_name: str
    timestamp: str
    architecture: str
    success: bool
    duration: float
    quality_score: float
    token_count: int
    cache_hits: int
    error_count: int
    agents_used: List[str]
    error_message: Optional[str] = None

class PerformanceRegressionTester:
    """Runs performance regression tests"""
    
    def __init__(self, use_new_architecture: bool = False):
        self.use_new_architecture = use_new_architecture
        self.adapter = ResearchManagerAdapter(use_new_architecture=use_new_architecture)
        self.results: List[TestResult] = []
        self.baseline: Optional[Dict[str, Any]] = None
        
        # Create results directory
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        # Load baseline if exists
        self._load_baseline()
    
    def _load_baseline(self):
        """Load performance baseline"""
        if os.path.exists(BASELINE_FILE):
            try:
                with open(BASELINE_FILE, 'r') as f:
                    self.baseline = json.load(f)
                logger.info(f"Loaded baseline from {self.baseline['timestamp']}")
            except Exception as e:
                logger.warning(f"Failed to load baseline: {e}")
    
    async def run_scenario(self, scenario: TestScenario) -> TestResult:
        """Run a single test scenario"""
        logger.info(f"Running scenario: {scenario.name}")
        start_time = time.time()
        
        # Warm up cache if needed
        if scenario.cache_warmup:
            logger.info("Warming up cache...")
            try:
                async for _ in self.adapter.run(scenario.query):
                    pass
            except:
                pass  # Ignore warmup errors
            await asyncio.sleep(1)
        
        # Initialize tracking
        success = False
        quality_score = 0.0
        token_count = 0
        cache_hits = 0
        error_count = 0
        agents_used = []
        error_message = None
        
        try:
            # Run the query
            full_output = []
            async for update in self.adapter.run(scenario.query):
                full_output.append(update)
            
            # Parse results
            output_text = '\n'.join(full_output)
            
            # Extract metrics
            if "Quality Score:" in output_text:
                score_line = [l for l in output_text.split('\n') if "Quality Score:" in l][0]
                quality_score = float(score_line.split(":")[-1].strip())
            
            # Count agent mentions
            for agent in ["clarifier", "planner", "search", "writer", "email"]:
                if agent in output_text.lower():
                    agents_used.append(agent)
                    if "enhanced" in output_text.lower() and agent in output_text.lower():
                        agents_used.append(f"enhanced_{agent}")
            
            # Estimate tokens (rough approximation)
            token_count = len(output_text.split()) * 1.3
            
            success = True
            
        except Exception as e:
            error_message = str(e)
            error_count = 1
            logger.error(f"Scenario {scenario.name} failed: {error_message}")
        
        duration = time.time() - start_time
        
        return TestResult(
            scenario_name=scenario.name,
            timestamp=datetime.now().isoformat(),
            architecture="new" if self.use_new_architecture else "old",
            success=success,
            duration=duration,
            quality_score=quality_score,
            token_count=int(token_count),
            cache_hits=cache_hits,
            error_count=error_count,
            agents_used=agents_used,
            error_message=error_message
        )
    
    async def run_all_scenarios(self):
        """Run all test scenarios"""
        logger.info(f"Running {len(TEST_SCENARIOS)} test scenarios...")
        
        for scenario in TEST_SCENARIOS:
            result = await self.run_scenario(scenario)
            self.results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        logger.info("All scenarios completed")
    
    def check_regressions(self) -> Dict[str, Any]:
        """Check for performance regressions against baseline"""
        if not self.baseline:
            logger.warning("No baseline available for comparison")
            return {"status": "no_baseline"}
        
        regressions = []
        improvements = []
        
        for result in self.results:
            # Find baseline for this scenario
            baseline_result = None
            for br in self.baseline.get("results", []):
                if br["scenario_name"] == result.scenario_name:
                    baseline_result = br
                    break
            
            if not baseline_result:
                continue
            
            # Compare performance
            duration_change = (result.duration - baseline_result["duration"]) / baseline_result["duration"]
            quality_change = (result.quality_score - baseline_result["quality_score"]) / (baseline_result["quality_score"] or 0.1)
            
            # Check for regressions
            if duration_change > REGRESSION_THRESHOLD:
                regressions.append({
                    "scenario": result.scenario_name,
                    "metric": "duration",
                    "baseline": baseline_result["duration"],
                    "current": result.duration,
                    "degradation": duration_change * 100
                })
            
            if quality_change < -REGRESSION_THRESHOLD:
                regressions.append({
                    "scenario": result.scenario_name,
                    "metric": "quality",
                    "baseline": baseline_result["quality_score"],
                    "current": result.quality_score,
                    "degradation": quality_change * 100
                })
            
            # Track improvements
            if duration_change < -0.1:  # 10% faster
                improvements.append({
                    "scenario": result.scenario_name,
                    "metric": "duration",
                    "improvement": -duration_change * 100
                })
        
        return {
            "status": "completed",
            "regressions": regressions,
            "improvements": improvements,
            "passed": len(regressions) == 0
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance test report"""
        # Calculate statistics
        successful_results = [r for r in self.results if r.success]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "architecture": "new" if self.use_new_architecture else "old",
            "summary": {
                "total_scenarios": len(self.results),
                "successful": len(successful_results),
                "failed": len(self.results) - len(successful_results),
                "success_rate": len(successful_results) / len(self.results) * 100 if self.results else 0
            }
        }
        
        if successful_results:
            report["performance"] = {
                "avg_duration": statistics.mean([r.duration for r in successful_results]),
                "avg_quality": statistics.mean([r.quality_score for r in successful_results if r.quality_score > 0]),
                "total_tokens": sum([r.token_count for r in successful_results])
            }
        
        # Add regression check results
        regression_check = self.check_regressions()
        report["regression_check"] = regression_check
        
        # Add detailed results
        report["results"] = [asdict(r) for r in self.results]
        
        return report
    
    def save_results(self, set_as_baseline: bool = False):
        """Save test results"""
        report = self.generate_report()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{RESULTS_DIR}/performance_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Results saved to {filename}")
        
        # Optionally set as new baseline
        if set_as_baseline:
            with open(BASELINE_FILE, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"New baseline set")
        
        return report

async def run_regression_tests(architecture: str = "old", set_baseline: bool = False):
    """Run performance regression tests"""
    use_new = architecture.lower() == "new"
    
    logger.info(f"Starting performance regression tests")
    logger.info(f"Architecture: {architecture}")
    logger.info(f"Set as baseline: {set_baseline}")
    
    # Create tester
    tester = PerformanceRegressionTester(use_new_architecture=use_new)
    
    # Run tests
    await tester.run_all_scenarios()
    
    # Generate and save report
    report = tester.save_results(set_as_baseline=set_baseline)
    
    # Print summary
    print("\n" + "="*60)
    print("PERFORMANCE REGRESSION TEST RESULTS")
    print("="*60)
    print(f"Architecture: {report['architecture']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    
    if 'performance' in report:
        print(f"\nPerformance Metrics:")
        print(f"  Average Duration: {report['performance']['avg_duration']:.2f}s")
        print(f"  Average Quality: {report['performance']['avg_quality']:.2f}")
        print(f"  Total Tokens: {report['performance']['total_tokens']}")
    
    # Print regression results
    if report['regression_check']['status'] == 'completed':
        regressions = report['regression_check']['regressions']
        improvements = report['regression_check']['improvements']
        
        if regressions:
            print(f"\n❌ REGRESSIONS DETECTED ({len(regressions)}):")
            for reg in regressions:
                print(f"  - {reg['scenario']}: {reg['metric']} degraded by {reg['degradation']:.1f}%")
                print(f"    Baseline: {reg['baseline']:.2f} → Current: {reg['current']:.2f}")
        
        if improvements:
            print(f"\n✅ IMPROVEMENTS ({len(improvements)}):")
            for imp in improvements:
                print(f"  - {imp['scenario']}: {imp['metric']} improved by {imp['improvement']:.1f}%")
        
        if not regressions:
            print("\n✅ All performance tests passed!")
    
    return report['regression_check'].get('passed', True)

# CLI interface
async def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run performance regression tests")
    parser.add_argument("--architecture", choices=["old", "new"], default="old",
                       help="Architecture to test")
    parser.add_argument("--set-baseline", action="store_true",
                       help="Set results as new baseline")
    parser.add_argument("--compare", action="store_true",
                       help="Run tests for both architectures and compare")
    
    args = parser.parse_args()
    
    if args.compare:
        # Test both architectures
        print("Testing OLD architecture...")
        old_passed = await run_regression_tests("old", False)
        
        print("\n" + "="*60 + "\n")
        
        print("Testing NEW architecture...")
        new_passed = await run_regression_tests("new", False)
        
        print("\n" + "="*60)
        print("COMPARISON COMPLETE")
        print(f"Old architecture: {'PASSED' if old_passed else 'FAILED'}")
        print(f"New architecture: {'PASSED' if new_passed else 'FAILED'}")
    else:
        # Test single architecture
        passed = await run_regression_tests(args.architecture, args.set_baseline)
        exit(0 if passed else 1)

if __name__ == "__main__":
    asyncio.run(main())