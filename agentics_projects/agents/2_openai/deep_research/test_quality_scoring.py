#!/usr/bin/env python3
# === TEST QUALITY SCORING INTEGRATION ===

from writer_agent import ReportData
from enhanced_writer_agent import EnhancedReportData
from performance_optimizer import performance_optimizer

def test_quality_scoring():
    """Test quality scoring for reports"""
    
    print("="*60)
    print("TESTING QUALITY SCORING INTEGRATION")
    print("="*60)
    
    # Test 1: Standard Report
    print("\n[TEST 1] Standard Report Quality Scoring")
    print("-"*40)
    
    report1 = ReportData(
        query="Test query",
        markdown_report="## Introduction\n\nThis is a test report.\n\n## Analysis\n\n- Point 1\n- Point 2\n\n## Conclusion\n\nTest complete.",
        word_count=1000,
        search_count=5
    )
    
    print(f"Before: quality_score = {report1.quality_score}")
    report1.calculate_quality()
    print(f"After: quality_score = {report1.quality_score:.2f}")
    
    # Test 2: Enhanced Report  
    print("\n[TEST 2] Enhanced Report Quality Scoring")
    print("-"*40)
    
    report2 = EnhancedReportData(
        query="Test query with preferences",
        markdown_report="## Executive Overview\n\nComprehensive analysis.\n\n## Key Findings\n\n- Finding 1\n- Finding 2\n- Finding 3\n\n## Strategic Implications\n\nDetailed implications.\n\n## Recommended Actions\n\n1. Action 1\n2. Action 2",
        word_count=1200,
        search_count=8,
        report_format="Executive Summary",
        target_audience="Business Leaders",
        readability_score="Professional",
        key_takeaways=["Takeaway 1", "Takeaway 2", "Takeaway 3", "Takeaway 4"],
        source_diversity={"total_domains": 6, "source_types": ["academic", "news", "industry"]}
    )
    
    print(f"Before: quality_score = {report2.quality_score}")
    report2.calculate_quality()
    print(f"After: quality_score = {report2.quality_score:.2f}")
    
    # Test 3: Quality Score Calculation Details
    print("\n[TEST 3] Quality Score Breakdown")
    print("-"*40)
    
    test_cases = [
        {"word_count": 500, "search_count": 2, "markdown_report": "Short report"},
        {"word_count": 900, "search_count": 5, "markdown_report": "## Good\n\n### Section\n\n- List"},
        {"word_count": 1500, "search_count": 10, "markdown_report": "## Complete\n\n### Details\n\n- Item 1\n- Item 2"},
    ]
    
    for i, test_data in enumerate(test_cases):
        score = performance_optimizer.calculate_quality_score(test_data)
        print(f"Test case {i+1}: word_count={test_data['word_count']}, search_count={test_data['search_count']} → quality={score:.2f}")
    
    print("\n" + "="*60)
    print("QUALITY SCORING TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_quality_scoring()