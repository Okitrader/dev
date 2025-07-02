#!/usr/bin/env python3
"""
Simulate Shadow Mode Data for Testing
Creates realistic shadow mode comparison data for analysis
"""

import json
import random
import os
from datetime import datetime, timedelta

# Create performance data directory
PERFORMANCE_DATA_DIR = os.getenv("PERFORMANCE_DATA_DIR", "./performance_data")
os.makedirs(PERFORMANCE_DATA_DIR, exist_ok=True)

# Sample queries for simulation
SAMPLE_QUERIES = [
    "What is machine learning?",
    "Explain quantum computing to a beginner",
    "Compare solar and wind energy efficiency",
    "How do neural networks work?",
    "What are the latest AI breakthroughs in 2024?",
    "Explain blockchain technology and its applications",
    "What are microservices in software architecture?",
    "How does 5G technology differ from 4G?",
    "What are the environmental impacts of electric vehicles?",
    "Explain CRISPR gene editing technology",
    "What is quantum entanglement?\n\nReport Preferences: Format=Technical Deep-Dive, Audience=Technical Experts",
    "Compare React vs Vue vs Angular\n\nReport Preferences: Format=Comparative Analysis, Audience=General Public",
    "Analyze cryptocurrency market trends\n\nReport Preferences: Format=Executive Summary, Audience=Business Leaders"
]

def generate_shadow_comparison(query: str, timestamp: datetime) -> dict:
    """Generate a realistic shadow mode comparison"""
    
    # Determine query complexity
    query_words = len(query.split())
    has_preferences = "Report Preferences:" in query
    
    # Base performance characteristics
    if query_words < 10:
        base_old_time = random.uniform(15, 25)
        base_new_time = random.uniform(10, 18)
        complexity = "simple"
    elif query_words < 30:
        base_old_time = random.uniform(25, 40)
        base_new_time = random.uniform(18, 30)
        complexity = "moderate"
    else:
        base_old_time = random.uniform(40, 70)
        base_new_time = random.uniform(28, 50)
        complexity = "complex"
    
    # Add variance
    old_time = base_old_time + random.uniform(-5, 5)
    new_time = base_new_time + random.uniform(-3, 3)
    
    # Quality scores (new architecture typically better)
    base_quality = 0.7 if not has_preferences else 0.75
    new_quality = base_quality + random.uniform(0.05, 0.20)
    
    # Success rates (new architecture slightly more reliable)
    old_success = random.random() > 0.05  # 95% success
    new_success = random.random() > 0.02  # 98% success
    
    # Word counts
    old_words = random.randint(600, 1200)
    new_words = random.randint(800, 1500)
    
    return {
        "timestamp": timestamp.isoformat(),
        "query": query,
        "complexity": complexity,
        "results": {
            "old": {
                "success": old_success,
                "execution_time": old_time if old_success else 0,
                "word_count": old_words if old_success else 0
            },
            "new": {
                "success": new_success,
                "execution_time": new_time if new_success else 0,
                "word_count": new_words if new_success else 0,
                "quality_score": new_quality if new_success else 0
            },
            "improvement": {
                "speed": ((old_time - new_time) / old_time * 100) if (old_success and new_success) else 0,
                "success_rate": 1 if (new_success and not old_success) else 0
            }
        }
    }

def simulate_shadow_data(hours: int = 48, comparisons_per_hour: int = 10):
    """Simulate shadow mode data over time"""
    comparisons = []
    
    # Generate comparisons
    current_time = datetime.now() - timedelta(hours=hours)
    
    for hour in range(hours):
        # Vary load by time of day
        hour_of_day = (current_time + timedelta(hours=hour)).hour
        if 9 <= hour_of_day <= 17:  # Business hours
            num_comparisons = comparisons_per_hour
        elif 6 <= hour_of_day <= 22:  # Active hours
            num_comparisons = comparisons_per_hour // 2
        else:  # Night hours
            num_comparisons = comparisons_per_hour // 4
        
        for _ in range(num_comparisons):
            # Random timestamp within the hour
            timestamp = current_time + timedelta(
                hours=hour,
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            # Random query
            query = random.choice(SAMPLE_QUERIES)
            
            # Generate comparison
            comparison = generate_shadow_comparison(query, timestamp)
            comparisons.append(comparison)
    
    # Save to file
    shadow_data = {
        "generated": datetime.now().isoformat(),
        "comparisons": comparisons
    }
    
    shadow_file = os.path.join(PERFORMANCE_DATA_DIR, "shadow_comparisons.json")
    with open(shadow_file, 'w') as f:
        json.dump(shadow_data, f, indent=2)
    
    print(f"Generated {len(comparisons)} shadow mode comparisons")
    print(f"Saved to: {shadow_file}")
    
    # Calculate summary statistics
    successful = [c for c in comparisons if 
                  c["results"]["old"]["success"] and 
                  c["results"]["new"]["success"]]
    
    if successful:
        avg_improvement = sum(c["results"]["improvement"]["speed"] for c in successful) / len(successful)
        print(f"\nSummary:")
        print(f"  Total comparisons: {len(comparisons)}")
        print(f"  Successful: {len(successful)} ({len(successful)/len(comparisons)*100:.1f}%)")
        print(f"  Average speed improvement: {avg_improvement:.1f}%")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulate shadow mode data")
    parser.add_argument("--hours", type=int, default=48,
                       help="Hours of data to simulate")
    parser.add_argument("--rate", type=int, default=10,
                       help="Comparisons per hour (during business hours)")
    
    args = parser.parse_args()
    
    simulate_shadow_data(args.hours, args.rate)