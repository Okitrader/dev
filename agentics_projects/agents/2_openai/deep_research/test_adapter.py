#!/usr/bin/env python3
# === TEST RESEARCH MANAGER ADAPTER ===

import asyncio
from research_manager_adapter import ResearchManagerAdapter, get_adapter_instance

async def test_adapter():
    """Test the adapter with both architectures"""
    
    query = "What are the key principles of DevOps?"
    
    print("="*60)
    print("TESTING RESEARCH MANAGER ADAPTER")
    print("="*60)
    
    # Test 1: Old architecture
    print("\n[TEST 1] Old Architecture")
    print("-"*40)
    adapter = ResearchManagerAdapter(use_new_architecture=False)
    print(f"Current architecture: {adapter.get_current_architecture()}")
    
    updates = []
    try:
        async for update in adapter.run(query):
            updates.append(update)
            if len(update) < 100:  # Only print short updates
                print(f"Update: {update}")
        print(f"✓ Old architecture completed with {len(updates)} updates")
    except Exception as e:
        print(f"✗ Old architecture failed: {str(e)}")
    
    # Test 2: New architecture  
    print("\n[TEST 2] New Architecture")
    print("-"*40)
    adapter.set_architecture(use_new=True)
    print(f"Current architecture: {adapter.get_current_architecture()}")
    
    updates = []
    try:
        async for update in adapter.run(query):
            updates.append(update)
            if len(update) < 100:  # Only print short updates
                print(f"Update: {update}")
        print(f"✓ New architecture completed with {len(updates)} updates")
    except Exception as e:
        print(f"✗ New architecture failed: {str(e)}")
    
    # Test 3: Performance summary
    print("\n[TEST 3] Performance Summary")
    print("-"*40)
    summary = adapter.get_performance_summary()
    print(json.dumps(summary, indent=2))
    
    # Test 4: Singleton instance
    print("\n[TEST 4] Singleton Instance")
    print("-"*40)
    instance1 = get_adapter_instance()
    instance2 = get_adapter_instance()
    print(f"Singleton test: {instance1 is instance2}")
    
    print("\n" + "="*60)
    print("ADAPTER TESTS COMPLETE")
    print("="*60)

import json

if __name__ == "__main__":
    asyncio.run(test_adapter())