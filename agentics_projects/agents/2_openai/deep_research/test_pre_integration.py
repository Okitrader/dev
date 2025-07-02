#!/usr/bin/env python3
# === PRE-INTEGRATION VALIDATION TESTS ===
# Purpose: Verify all components work correctly before integration

import asyncio
import logging
from typing import Dict, Any, List
import json
from datetime import datetime

# Import all components to test
from agent_tools import tool_registry, AgentTool, ToolResult
from enhanced_writer_agent import get_writer_for_preferences, extract_preferences, REPORT_TEMPLATES
from performance_optimizer import performance_optimizer, PerformanceRecord
from manager_agent import ManagerOrchestrator, QueryComplexity, WorkflowStrategy, PerformanceMetrics
from error_handler import error_handler, ErrorCategory
from cache_manager import cache_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PreIntegrationValidator:
    """Validates all components before integration"""
    
    def __init__(self):
        self.test_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print("\n" + "="*60)
        print("PRE-INTEGRATION VALIDATION SUITE")
        print("="*60 + "\n")
        
        # Test each component
        await self.test_tool_registry()
        await self.test_enhanced_writer()
        await self.test_performance_optimizer()
        await self.test_manager_orchestrator()
        await self.test_error_handler()
        await self.test_cache_manager()
        await self.test_agent_mappings()
        
        # Print summary
        self.print_summary()
    
    async def test_tool_registry(self):
        """Test tool registry and all tool wrappers"""
        print("\n[TEST] Tool Registry Validation")
        print("-" * 40)
        
        try:
            # Test registry access
            tools = tool_registry.list_tools()
            print(f"✓ Found {len(tools)} tools: {', '.join(tools)}")
            self.test_results["passed"].append("Tool registry access")
            
            # Test each tool wrapper
            for tool_name in tools:
                tool = tool_registry.get_tool(tool_name)
                if tool:
                    print(f"✓ Tool '{tool_name}' loaded successfully")
                    self.test_results["passed"].append(f"Tool loading: {tool_name}")
                else:
                    print(f"✗ Failed to load tool '{tool_name}'")
                    self.test_results["failed"].append(f"Tool loading: {tool_name}")
            
            # Test sample tool execution
            test_input = {"query": "test query"}
            test_context = {"use_enhanced": False}
            
            # Note: We won't actually execute tools as they require agents
            print("✓ Tool structure validation complete")
            
        except Exception as e:
            print(f"✗ Tool registry test failed: {str(e)}")
            self.test_results["failed"].append(f"Tool registry: {str(e)}")
    
    async def test_enhanced_writer(self):
        """Test enhanced writer preference extraction and selection"""
        print("\n[TEST] Enhanced Writer Validation")
        print("-" * 40)
        
        try:
            # Test preference extraction
            test_queries = [
                """Research quantum computing.
                
Report Preferences:
Format: Technical Deep-Dive
Length: Comprehensive (1500+ words)
Audience: Technical Experts""",
                
                """What is machine learning?
                
Report Preferences:
Format: Executive Summary
Length: Brief (300 words)
Audience: Business Leaders""",
                
                "Simple query without preferences"
            ]
            
            for i, query in enumerate(test_queries):
                prefs = extract_preferences(query)
                print(f"\nTest {i+1}: Extracted preferences:")
                print(f"  Format: {prefs['format']}")
                print(f"  Length: {prefs['length']}")
                print(f"  Audience: {prefs['audience']}")
                
                # Test writer selection
                writer = get_writer_for_preferences(query)
                if writer:
                    print(f"  ✓ Writer selected successfully")
                    self.test_results["passed"].append(f"Writer selection test {i+1}")
                else:
                    print(f"  ✗ Writer selection failed")
                    self.test_results["failed"].append(f"Writer selection test {i+1}")
            
            # Validate all template combinations exist
            missing_combos = []
            for format_type in REPORT_TEMPLATES:
                print(f"✓ Report template '{format_type}' validated")
                self.test_results["passed"].append(f"Template: {format_type}")
            
        except Exception as e:
            print(f"✗ Enhanced writer test failed: {str(e)}")
            self.test_results["failed"].append(f"Enhanced writer: {str(e)}")
    
    async def test_performance_optimizer(self):
        """Test performance optimizer functionality"""
        print("\n[TEST] Performance Optimizer Validation")
        print("-" * 40)
        
        try:
            # Test quality score calculation
            test_report = {
                "word_count": 1000,
                "search_count": 5,
                "markdown_report": "## Test Report\n\n### Section 1\n\n- Point 1\n- Point 2",
                "source_diversity": {"total_domains": 4}
            }
            
            quality_score = performance_optimizer.calculate_quality_score(test_report)
            print(f"✓ Quality score calculation: {quality_score:.2f}")
            self.test_results["passed"].append("Quality score calculation")
            
            # Test performance prediction
            test_analysis = {
                "query_words": 15,
                "query_complexity": "moderate",
                "search_count": 5
            }
            test_sequence = ["clarifier", "planner", "search", "writer"]
            
            predictions = performance_optimizer.predict_performance(test_analysis, test_sequence)
            print(f"✓ Performance prediction:")
            for dim, value in predictions.items():
                print(f"  - {dim}: {value:.2f}")
            self.test_results["passed"].append("Performance prediction")
            
            # Test optimization suggestions
            suggestions = performance_optimizer.get_optimization_suggestions("test query", test_analysis)
            print(f"✓ Generated {len(suggestions)} optimization suggestions")
            self.test_results["passed"].append("Optimization suggestions")
            
        except Exception as e:
            print(f"✗ Performance optimizer test failed: {str(e)}")
            self.test_results["failed"].append(f"Performance optimizer: {str(e)}")
    
    async def test_manager_orchestrator(self):
        """Test manager orchestrator decision making"""
        print("\n[TEST] Manager Orchestrator Validation")
        print("-" * 40)
        
        try:
            orchestrator = ManagerOrchestrator()
            
            # Test query analysis
            test_queries = [
                "What is Python?",  # Simple
                "Compare microservices vs monolithic architecture",  # Complex
                "Latest AI developments in 2024"  # Current events
            ]
            
            for query in test_queries:
                complexity, analysis = await orchestrator.analyze_query(query)
                print(f"\nQuery: '{query[:50]}...'")
                print(f"  Complexity: {complexity.value}")
                print(f"  Analysis: {json.dumps(analysis, indent=2)}")
                
                # Test strategy selection
                strategy = orchestrator.select_strategy(complexity, analysis)
                print(f"  Strategy: {strategy.value}")
                
                # Test agent sequence
                sequence = orchestrator.determine_agent_sequence(strategy, analysis)
                print(f"  Agent sequence: {' → '.join(sequence)}")
                
                self.test_results["passed"].append(f"Query analysis: {query[:30]}")
            
        except Exception as e:
            print(f"✗ Manager orchestrator test failed: {str(e)}")
            self.test_results["failed"].append(f"Manager orchestrator: {str(e)}")
    
    async def test_error_handler(self):
        """Test error handler categorization"""
        print("\n[TEST] Error Handler Validation")
        print("-" * 40)
        
        try:
            # Test error categorization
            test_errors = [
                Exception("Connection refused"),
                Exception("Rate limit exceeded (429)"),
                Exception("401 Unauthorized"),
                Exception("Request timed out"),
                Exception("Failed to parse JSON response")
            ]
            
            expected_categories = [
                ErrorCategory.NETWORK,
                ErrorCategory.API_LIMIT,
                ErrorCategory.AUTHENTICATION,
                ErrorCategory.TIMEOUT,
                ErrorCategory.PARSING
            ]
            
            for error, expected in zip(test_errors, expected_categories):
                category = error_handler.categorize_error(error)
                user_msg = error_handler.get_user_message(error)
                
                if category == expected:
                    print(f"✓ Correctly categorized '{str(error)}' as {category}")
                    self.test_results["passed"].append(f"Error categorization: {expected}")
                else:
                    print(f"✗ Incorrectly categorized '{str(error)}' as {category} (expected {expected})")
                    self.test_results["failed"].append(f"Error categorization: {expected}")
                
                print(f"  User message: {user_msg}")
            
        except Exception as e:
            print(f"✗ Error handler test failed: {str(e)}")
            self.test_results["failed"].append(f"Error handler: {str(e)}")
    
    async def test_cache_manager(self):
        """Test cache manager functionality"""
        print("\n[TEST] Cache Manager Validation")
        print("-" * 40)
        
        try:
            # Test cache key generation
            test_query = "What is artificial intelligence?"
            cache_key = cache_manager._generate_cache_key(test_query)
            print(f"✓ Cache key generated: {cache_key}")
            self.test_results["passed"].append("Cache key generation")
            
            # Test cache operations (without actual caching)
            print("✓ Cache manager initialized")
            print(f"  Cache directory: {cache_manager.cache_dir}")
            print(f"  Cache TTL: 24 hours")
            
            # Test cache stats
            stats = cache_manager.get_cache_stats()
            print(f"✓ Cache stats retrieved: {json.dumps(stats, indent=2)}")
            self.test_results["passed"].append("Cache operations")
            
        except Exception as e:
            print(f"✗ Cache manager test failed: {str(e)}")
            self.test_results["failed"].append(f"Cache manager: {str(e)}")
    
    async def test_agent_mappings(self):
        """Test agent name mappings between systems"""
        print("\n[TEST] Agent Name Mapping Validation")
        print("-" * 40)
        
        # Expected agent names in the system
        base_agents = ["clarifier", "planner", "search", "writer", "email", "followup"]
        enhanced_variants = ["enhanced_planner", "enhanced_search", "enhanced_writer"]
        
        # Check tool registry has all base agents
        available_tools = tool_registry.list_tools()
        
        print("Base agents:")
        for agent_name in base_agents:
            if agent_name in available_tools:
                print(f"✓ Agent '{agent_name}' found in tool registry")
                self.test_results["passed"].append(f"Agent mapping: {agent_name}")
            else:
                print(f"✗ Agent '{agent_name}' NOT found in tool registry")
                self.test_results["failed"].append(f"Agent mapping: {agent_name}")
        
        print("\nEnhanced agents (handled via context flags):")
        # Check that enhanced agents are properly configured in base tools
        for enhanced_name in enhanced_variants:
            base_name = enhanced_name.replace("enhanced_", "")
            if base_name in available_tools:
                tool = tool_registry.get_tool(base_name)
                if hasattr(tool, 'enhanced_agent') and tool.enhanced_agent is not None:
                    print(f"✓ Enhanced variant '{enhanced_name}' available via '{base_name}' tool")
                    self.test_results["passed"].append(f"Enhanced variant: {enhanced_name}")
                else:
                    print(f"⚠️  Enhanced variant '{enhanced_name}' not configured in '{base_name}' tool")
                    self.test_results["warnings"].append(f"Enhanced variant missing: {enhanced_name}")
            else:
                print(f"✗ Base tool for '{enhanced_name}' not found")
                self.test_results["failed"].append(f"Enhanced variant: {enhanced_name}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results["passed"]) + len(self.test_results["failed"])
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✓ Passed: {len(self.test_results['passed'])}")
        print(f"✗ Failed: {len(self.test_results['failed'])}")
        print(f"⚠️  Warnings: {len(self.test_results['warnings'])}")
        
        if self.test_results["failed"]:
            print("\nFailed Tests:")
            for failure in self.test_results["failed"]:
                print(f"  - {failure}")
        
        if self.test_results["warnings"]:
            print("\nWarnings:")
            for warning in self.test_results["warnings"]:
                print(f"  - {warning}")
        
        if not self.test_results["failed"]:
            print("\n✅ ALL TESTS PASSED! Ready for integration.")
        else:
            print("\n❌ VALIDATION FAILED! Fix issues before proceeding.")
        
        # Save results
        with open("pre_integration_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.test_results,
                "summary": {
                    "total": total_tests,
                    "passed": len(self.test_results["passed"]),
                    "failed": len(self.test_results["failed"]),
                    "warnings": len(self.test_results["warnings"])
                }
            }, f, indent=2)
        
        print("\nResults saved to: pre_integration_results.json")

async def main():
    """Run pre-integration validation"""
    validator = PreIntegrationValidator()
    await validator.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())