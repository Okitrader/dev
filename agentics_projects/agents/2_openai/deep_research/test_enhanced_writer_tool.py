#!/usr/bin/env python3
# === TEST ENHANCED WRITER TOOL INTEGRATION ===

import asyncio
from agent_tools import tool_registry
from enhanced_writer_agent import extract_preferences

async def test_enhanced_writer_tool():
    """Test enhanced writer tool integration"""
    
    print("="*60)
    print("TESTING ENHANCED WRITER TOOL INTEGRATION")
    print("="*60)
    
    # Get writer tool
    writer_tool = tool_registry.get_tool("writer")
    if not writer_tool:
        print("✗ Failed to get writer tool")
        return
    
    print("✓ Writer tool loaded successfully")
    
    # Test cases
    test_cases = [
        {
            "name": "Standard Report (no preferences)",
            "input": {
                "query": "What is cloud computing?",
                "search_results": [
                    "Cloud computing is the delivery of computing services over the internet.",
                    "Major providers include AWS, Azure, and Google Cloud.",
                    "Benefits include scalability, cost-effectiveness, and flexibility."
                ]
            }
        },
        {
            "name": "Enhanced Report with Preferences",
            "input": {
                "query": """Research quantum computing applications.
                
Report Preferences:
Format: Technical Deep-Dive
Length: Comprehensive (1500+ words)
Audience: Technical Experts""",
                "search_results": [
                    "Quantum computing uses quantum mechanics principles for computation.",
                    "Applications include cryptography, drug discovery, and optimization.",
                    "Current challenges include decoherence and error rates.",
                    "Major players: IBM, Google, Microsoft, and various startups."
                ]
            }
        },
        {
            "name": "Business-Oriented Report",
            "input": {
                "query": """Analyze market trends in AI.

Report Preferences:
Format: Executive Summary
Length: Brief (300 words)
Audience: Business Leaders""",
                "search_results": [
                    "AI market expected to reach $1.8 trillion by 2030.",
                    "Key growth drivers: automation, data analytics, customer experience.",
                    "Leading sectors: healthcare, finance, retail, manufacturing."
                ]
            }
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases):
        print(f"\n[TEST {i+1}] {test_case['name']}")
        print("-"*40)
        
        # Extract preferences if present
        prefs = extract_preferences(test_case["input"]["query"])
        print(f"Preferences detected:")
        print(f"  Format: {prefs['format']}")
        print(f"  Length: {prefs['length']}")
        print(f"  Audience: {prefs['audience']}")
        
        # Run writer tool
        context = {}
        result = await writer_tool.run(test_case["input"], context)
        
        if result.success:
            print(f"✓ Report generated successfully")
            if result.result:
                print(f"  Word count: {result.result.word_count}")
                print(f"  Quality score: {result.result.quality_score:.2f}")
                print(f"  Used enhanced writer: {context.get('use_enhanced_writer', False)}")
        else:
            print(f"✗ Failed: {result.error_message}")
    
    print("\n" + "="*60)
    print("ENHANCED WRITER TOOL TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_enhanced_writer_tool())