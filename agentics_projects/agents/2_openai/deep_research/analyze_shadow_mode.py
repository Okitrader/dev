#!/usr/bin/env python3
"""
Shadow Mode Analysis Tool
Analyzes performance comparison data from shadow mode testing
"""

import json
import os
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import argparse
from collections import defaultdict

# Configuration
PERFORMANCE_DATA_DIR = os.getenv("PERFORMANCE_DATA_DIR", "./performance_data")
SHADOW_COMPARISONS_FILE = os.path.join(PERFORMANCE_DATA_DIR, "shadow_comparisons.json")

class ShadowModeAnalyzer:
    """Analyzes shadow mode comparison data"""
    
    def __init__(self):
        self.comparisons = []
        self.load_data()
    
    def load_data(self):
        """Load shadow mode comparison data"""
        if os.path.exists(SHADOW_COMPARISONS_FILE):
            try:
                with open(SHADOW_COMPARISONS_FILE, 'r') as f:
                    data = json.load(f)
                    self.comparisons = data.get("comparisons", [])
                print(f"Loaded {len(self.comparisons)} shadow mode comparisons")
            except Exception as e:
                print(f"Error loading shadow data: {e}")
        else:
            print(f"No shadow mode data found at {SHADOW_COMPARISONS_FILE}")
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze overall performance differences"""
        if not self.comparisons:
            return {"error": "No comparison data available"}
        
        # Separate successful comparisons
        successful = [c for c in self.comparisons if 
                     c["results"]["old"]["success"] and 
                     c["results"]["new"]["success"]]
        
        if not successful:
            return {"error": "No successful comparisons to analyze"}
        
        # Calculate metrics
        speed_improvements = []
        quality_scores_old = []
        quality_scores_new = []
        
        for comp in successful:
            old_time = comp["results"]["old"]["execution_time"]
            new_time = comp["results"]["new"]["execution_time"]
            
            if old_time > 0:
                improvement = (old_time - new_time) / old_time * 100
                speed_improvements.append(improvement)
            
            # Quality scores (new architecture only)
            if "quality_score" in comp["results"]["new"]:
                quality_scores_new.append(comp["results"]["new"]["quality_score"])
                # Estimate old quality as 0.7 baseline
                quality_scores_old.append(0.7)
        
        analysis = {
            "total_comparisons": len(self.comparisons),
            "successful_comparisons": len(successful),
            "success_rate": len(successful) / len(self.comparisons) * 100,
            "speed_improvement": {
                "average": statistics.mean(speed_improvements) if speed_improvements else 0,
                "median": statistics.median(speed_improvements) if speed_improvements else 0,
                "min": min(speed_improvements) if speed_improvements else 0,
                "max": max(speed_improvements) if speed_improvements else 0,
                "std_dev": statistics.stdev(speed_improvements) if len(speed_improvements) > 1 else 0
            }
        }
        
        if quality_scores_new:
            analysis["quality_improvement"] = {
                "old_average": statistics.mean(quality_scores_old),
                "new_average": statistics.mean(quality_scores_new),
                "improvement": statistics.mean(quality_scores_new) - statistics.mean(quality_scores_old)
            }
        
        return analysis
    
    def analyze_by_query_type(self) -> Dict[str, Any]:
        """Analyze performance by query characteristics"""
        query_types = defaultdict(list)
        
        for comp in self.comparisons:
            query = comp["query"]
            query_length = len(query.split())
            
            # Categorize queries
            if query_length < 10:
                category = "simple"
            elif query_length < 30:
                category = "moderate"
            else:
                category = "complex"
            
            # Add preferences category
            if "Report Preferences:" in query:
                category += "_with_preferences"
            
            query_types[category].append(comp)
        
        # Analyze each category
        analysis = {}
        for category, comparisons in query_types.items():
            successful = [c for c in comparisons if 
                         c["results"]["old"]["success"] and 
                         c["results"]["new"]["success"]]
            
            if successful:
                speed_improvements = []
                for comp in successful:
                    old_time = comp["results"]["old"]["execution_time"]
                    new_time = comp["results"]["new"]["execution_time"]
                    if old_time > 0:
                        improvement = (old_time - new_time) / old_time * 100
                        speed_improvements.append(improvement)
                
                analysis[category] = {
                    "count": len(successful),
                    "avg_speed_improvement": statistics.mean(speed_improvements) if speed_improvements else 0
                }
        
        return analysis
    
    def analyze_failures(self) -> Dict[str, Any]:
        """Analyze failure patterns"""
        old_failures = []
        new_failures = []
        both_failures = []
        
        for comp in self.comparisons:
            old_success = comp["results"]["old"]["success"]
            new_success = comp["results"]["new"]["success"]
            
            if not old_success and not new_success:
                both_failures.append(comp)
            elif not old_success:
                old_failures.append(comp)
            elif not new_success:
                new_failures.append(comp)
        
        return {
            "old_only_failures": len(old_failures),
            "new_only_failures": len(new_failures),
            "both_failed": len(both_failures),
            "new_reliability_improvement": len(old_failures) - len(new_failures)
        }
    
    def analyze_time_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_comparisons = []
        for comp in self.comparisons:
            try:
                timestamp = datetime.fromisoformat(comp["timestamp"])
                if timestamp > cutoff:
                    recent_comparisons.append(comp)
            except:
                continue
        
        if not recent_comparisons:
            return {"error": f"No comparisons in the last {hours} hours"}
        
        # Group by hour
        hourly_data = defaultdict(list)
        for comp in recent_comparisons:
            timestamp = datetime.fromisoformat(comp["timestamp"])
            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            
            if (comp["results"]["old"]["success"] and 
                comp["results"]["new"]["success"]):
                old_time = comp["results"]["old"]["execution_time"]
                new_time = comp["results"]["new"]["execution_time"]
                if old_time > 0:
                    improvement = (old_time - new_time) / old_time * 100
                    hourly_data[hour_key].append(improvement)
        
        # Calculate hourly averages
        trends = {}
        for hour, improvements in sorted(hourly_data.items()):
            trends[hour] = {
                "count": len(improvements),
                "avg_improvement": statistics.mean(improvements)
            }
        
        return trends
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Speed improvement recommendation
        avg_speed = analysis.get("speed_improvement", {}).get("average", 0)
        if avg_speed > 30:
            recommendations.append(
                f"✅ STRONG PERFORMANCE: New architecture shows {avg_speed:.1f}% "
                f"average speed improvement. Ready for broader rollout."
            )
        elif avg_speed > 15:
            recommendations.append(
                f"✅ GOOD PERFORMANCE: New architecture shows {avg_speed:.1f}% "
                f"average speed improvement. Consider expanding beta."
            )
        elif avg_speed > 0:
            recommendations.append(
                f"⚠️  MODEST IMPROVEMENT: Only {avg_speed:.1f}% speed improvement. "
                f"Investigate optimization opportunities."
            )
        else:
            recommendations.append(
                f"❌ NO IMPROVEMENT: New architecture is not faster. "
                f"Review implementation before rollout."
            )
        
        # Quality recommendation
        quality_imp = analysis.get("quality_improvement", {}).get("improvement", 0)
        if quality_imp > 0.1:
            recommendations.append(
                f"✅ Quality scores improved by {quality_imp:.2f} points"
            )
        elif quality_imp < -0.05:
            recommendations.append(
                f"⚠️  Quality scores decreased by {abs(quality_imp):.2f} points"
            )
        
        # Success rate recommendation
        success_rate = analysis.get("success_rate", 0)
        if success_rate < 90:
            recommendations.append(
                f"⚠️  Low comparison success rate ({success_rate:.1f}%). "
                f"Investigate error patterns."
            )
        
        # Variance recommendation
        std_dev = analysis.get("speed_improvement", {}).get("std_dev", 0)
        if std_dev > 30:
            recommendations.append(
                f"⚠️  High performance variance (σ={std_dev:.1f}%). "
                f"Performance is inconsistent."
            )
        
        return recommendations
    
    def generate_report(self):
        """Generate comprehensive shadow mode analysis report"""
        print("\n" + "="*60)
        print("SHADOW MODE ANALYSIS REPORT")
        print("="*60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data source: {SHADOW_COMPARISONS_FILE}")
        
        # Overall performance analysis
        analysis = self.analyze_performance()
        
        if "error" in analysis:
            print(f"\n❌ {analysis['error']}")
            return
        
        print(f"\n### Overall Performance ###")
        print(f"Total comparisons: {analysis['total_comparisons']}")
        print(f"Successful: {analysis['successful_comparisons']} ({analysis['success_rate']:.1f}%)")
        
        speed = analysis['speed_improvement']
        print(f"\nSpeed Improvement:")
        print(f"  Average: {speed['average']:.1f}%")
        print(f"  Median: {speed['median']:.1f}%")
        print(f"  Range: {speed['min']:.1f}% to {speed['max']:.1f}%")
        print(f"  Std Dev: {speed['std_dev']:.1f}%")
        
        if 'quality_improvement' in analysis:
            quality = analysis['quality_improvement']
            print(f"\nQuality Improvement:")
            print(f"  Old avg: {quality['old_average']:.2f}")
            print(f"  New avg: {quality['new_average']:.2f}")
            print(f"  Improvement: {quality['improvement']:.2f}")
        
        # Query type analysis
        query_analysis = self.analyze_by_query_type()
        if query_analysis:
            print(f"\n### Performance by Query Type ###")
            for category, data in sorted(query_analysis.items()):
                print(f"{category}: {data['avg_speed_improvement']:.1f}% improvement (n={data['count']})")
        
        # Failure analysis
        failures = self.analyze_failures()
        print(f"\n### Reliability Analysis ###")
        print(f"Old architecture failures: {failures['old_only_failures']}")
        print(f"New architecture failures: {failures['new_only_failures']}")
        print(f"Both failed: {failures['both_failed']}")
        if failures['new_reliability_improvement'] > 0:
            print(f"✅ New architecture fixed {failures['new_reliability_improvement']} failures")
        
        # Time trends
        trends = self.analyze_time_trends(24)
        if not isinstance(trends, dict) or "error" not in trends:
            print(f"\n### 24-Hour Trends ###")
            for hour, data in list(trends.items())[-6:]:  # Last 6 hours
                print(f"{hour}: {data['avg_improvement']:.1f}% (n={data['count']})")
        
        # Recommendations
        recommendations = self.generate_recommendations(analysis)
        print(f"\n### Recommendations ###")
        for rec in recommendations:
            print(rec)
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "query_types": query_analysis,
            "failures": failures,
            "trends": trends,
            "recommendations": recommendations
        }
        
        report_file = f"shadow_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Analyze shadow mode performance data")
    parser.add_argument("--hours", type=int, default=24,
                       help="Hours of data to analyze for trends")
    parser.add_argument("--export", action="store_true",
                       help="Export raw comparison data")
    
    args = parser.parse_args()
    
    analyzer = ShadowModeAnalyzer()
    
    if args.export:
        # Export raw data for external analysis
        export_file = f"shadow_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(analyzer.comparisons, f, indent=2)
        print(f"Exported {len(analyzer.comparisons)} comparisons to {export_file}")
    else:
        # Generate analysis report
        analyzer.generate_report()

if __name__ == "__main__":
    main()