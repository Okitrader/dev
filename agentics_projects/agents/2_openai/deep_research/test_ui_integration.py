#!/usr/bin/env python3
# === TEST UI INTEGRATION ===
# Purpose: Verify the ResearchManagerAdapter is properly integrated with the UI

import asyncio
import os

# Test the imports work
try:
    from research_manager_adapter import ResearchManagerAdapter
    print("✓ ResearchManagerAdapter imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ResearchManagerAdapter: {e}")
    exit(1)

# Test environment variable handling
print("\n[TEST] Environment Variable Handling")
print("-" * 40)

# Test default (should be False)
os.environ.pop("USE_NEW_ARCHITECTURE", None)  # Remove if exists
adapter1 = ResearchManagerAdapter()
print(f"Default architecture: {adapter1.get_current_architecture()}")

# Test with env var set to true
os.environ["USE_NEW_ARCHITECTURE"] = "true"
adapter2 = ResearchManagerAdapter()
print(f"With USE_NEW_ARCHITECTURE=true: {adapter2.get_current_architecture()}")

# Test with env var set to false
os.environ["USE_NEW_ARCHITECTURE"] = "false"
adapter3 = ResearchManagerAdapter()
print(f"With USE_NEW_ARCHITECTURE=false: {adapter3.get_current_architecture()}")

# Test explicit parameter overrides env var
adapter4 = ResearchManagerAdapter(use_new_architecture=True)
print(f"Explicit True (overrides env): {adapter4.get_current_architecture()}")

# Test UI integration
print("\n[TEST] UI Parameter Handling")
print("-" * 40)

async def test_ui_run():
    """Simulate UI run function call"""
    from deep_research import run
    
    # Test parameters
    query = "What is cloud computing?"
    report_format = "Executive Summary"
    report_length = "Brief (300 words)"
    target_audience = "General Public"
    use_enhanced_features = True
    use_new_architecture = False  # Start with old architecture
    
    print(f"Testing with new architecture = {use_new_architecture}")
    
    # Simulate first few updates
    update_count = 0
    async for update in run(query, report_format, report_length, target_audience, 
                          use_enhanced_features, use_new_architecture):
        update_count += 1
        if update_count <= 3:  # Show first 3 updates
            if len(update) == 4:  # New format with performance data
                status, report, perf_visible, perf_text = update
                print(f"Update {update_count}: Status lines: {len(status.split(chr(10)))}, "
                      f"Performance visible: {perf_visible}")
            else:
                print(f"Update {update_count}: Unexpected format")
        
        # Stop after a few updates to avoid full research
        if update_count >= 5:
            print("... (stopped after 5 updates)")
            break

# Run async test
print("\nRunning async UI test...")
try:
    asyncio.run(test_ui_run())
    print("✓ UI integration test completed")
except Exception as e:
    print(f"✗ UI integration test failed: {e}")

print("\n" + "="*60)
print("UI INTEGRATION TESTS COMPLETE")
print("="*60)