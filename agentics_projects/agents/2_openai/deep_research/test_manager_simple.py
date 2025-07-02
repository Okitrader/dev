#!/usr/bin/env python3
# === SIMPLE TEST FOR MANAGER ARCHITECTURE ===

import asyncio
from integrated_research_manager import run_intelligent_research

async def main():
    """Test the new architecture with a simple query"""
    print("🚀 Testing Manager-as-Agent Architecture\n")
    
    query = "What are the key benefits of microservices architecture?"
    
    print(f"Query: {query}\n")
    print("-" * 60)
    
    async for update in run_intelligent_research(query):
        print(update)

if __name__ == "__main__":
    asyncio.run(main())