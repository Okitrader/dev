"""
Load Testing for Deep Research System using Locust
Tests concurrent user performance and system scalability
"""

from locust import HttpUser, task, between
import json
import random
import time
from datetime import datetime

# Sample queries for testing
SAMPLE_QUERIES = [
    "What are the latest developments in quantum computing?",
    "Explain the impact of AI on healthcare in 2024",
    "Compare renewable energy sources: solar vs wind power",
    "What are the best practices for microservices architecture?",
    "Analyze the current state of electric vehicle adoption",
    "How does blockchain technology work in supply chain management?",
    "What are the environmental impacts of cryptocurrency mining?",
    "Explain machine learning algorithms for beginners",
    "What are the trends in cybersecurity for 2024?",
    "How do neural networks process natural language?"
]

# Preferences for enhanced testing
REPORT_PREFERENCES = [
    "",  # No preferences (standard)
    "Report Preferences: Format=Executive Summary, Audience=Business Leaders",
    "Report Preferences: Format=Technical Deep-Dive, Audience=Technical Experts",
    "Report Preferences: Format=Comparative Analysis, Audience=General Public"
]

class DeepResearchUser(HttpUser):
    """Simulates a user of the Deep Research System"""
    
    # Wait between 5-15 seconds between requests
    wait_time = between(5, 15)
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.session_id = f"load_test_{int(time.time())}_{random.randint(1000, 9999)}"
        self.architecture = random.choice(["old", "new"]) if random.random() < 0.5 else None
        
    @task(weight=3)
    def research_standard_query(self):
        """Submit a standard research query"""
        query = random.choice(SAMPLE_QUERIES)
        
        # Simulate form data similar to Gradio
        payload = {
            "query": query,
            "send_email": False,
            "use_new_architecture": self.architecture
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/api/research",
            json=payload,
            catch_response=True,
            name="research_standard"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    execution_time = time.time() - start_time
                    
                    # Validate response
                    if "report" in result and len(result["report"]) > 100:
                        response.success()
                        
                        # Log performance metrics
                        self.environment.stats.log_request(
                            "research_metrics",
                            "POST",
                            execution_time * 1000,  # Convert to ms
                            len(response.content)
                        )
                    else:
                        response.failure("Invalid response format")
                except Exception as e:
                    response.failure(f"Failed to parse response: {str(e)}")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(weight=1)
    def research_with_preferences(self):
        """Submit a research query with preferences"""
        base_query = random.choice(SAMPLE_QUERIES)
        preferences = random.choice(REPORT_PREFERENCES[1:])  # Skip empty preferences
        query = f"{base_query}\n\n{preferences}"
        
        payload = {
            "query": query,
            "send_email": False,
            "use_new_architecture": self.architecture
        }
        
        with self.client.post(
            "/api/research",
            json=payload,
            catch_response=True,
            name="research_enhanced"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(weight=1)
    def check_health(self):
        """Check system health"""
        with self.client.get("/health", name="health_check") as response:
            if response.status_code != 200:
                print(f"Health check failed: {response.status_code}")
    
    @task(weight=1)
    def get_metrics(self):
        """Get system metrics"""
        with self.client.get("/metrics", name="metrics") as response:
            if response.status_code != 200:
                print(f"Metrics endpoint failed: {response.status_code}")

class AdminUser(HttpUser):
    """Simulates an admin checking system status"""
    
    wait_time = between(30, 60)  # Check less frequently
    
    @task
    def check_shadow_performance(self):
        """Check shadow mode performance data"""
        with self.client.get("/api/performance/shadow", name="shadow_data") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "comparisons" in data:
                        # Log average performance improvement
                        comparisons = data["comparisons"]
                        if comparisons:
                            avg_improvement = sum(
                                c["results"]["improvement"]["speed"] 
                                for c in comparisons
                            ) / len(comparisons)
                            print(f"Average speed improvement: {avg_improvement:.1f}%")
                except Exception as e:
                    print(f"Failed to parse shadow data: {e}")
    
    @task
    def check_alerts(self):
        """Check for system alerts"""
        with self.client.get("/alerts", name="alerts") as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data["alerts"]:
                        print(f"Active alerts: {len(data['alerts'])}")
                        for alert in data["alerts"][-5:]:
                            print(f"  - {alert['message']}")
                except Exception as e:
                    print(f"Failed to parse alerts: {e}")


# Custom test scenarios
class StressTestUser(DeepResearchUser):
    """Aggressive user for stress testing"""
    wait_time = between(1, 3)  # Much shorter wait times
    
    def on_start(self):
        super().on_start()
        # Force new architecture for stress testing
        self.architecture = "new"


# Configuration for different test scenarios
"""
Usage:

1. Basic Load Test (50 users over 5 minutes):
   locust -f load_test_locust.py --host=http://localhost:7860 --users=50 --spawn-rate=2 --run-time=5m

2. Stress Test (200 users):
   locust -f load_test_locust.py --host=http://localhost:7860 --users=200 --spawn-rate=10 --run-time=10m --class=StressTestUser

3. Mixed Load (Users + Admins):
   locust -f load_test_locust.py --host=http://localhost:7860 --users=100 --spawn-rate=5

4. Web UI Mode:
   locust -f load_test_locust.py --host=http://localhost:7860
   Then open http://localhost:8089

5. Headless with CSV output:
   locust -f load_test_locust.py --host=http://localhost:7860 --users=100 --spawn-rate=5 --run-time=10m --headless --csv=results/load_test

Key Metrics to Monitor:
- Response time percentiles (p50, p90, p95)
- Requests per second
- Failure rate
- Active user count
- Response time trends
"""

if __name__ == "__main__":
    print("Deep Research Load Testing")
    print("Run with: locust -f load_test_locust.py --host=http://localhost:7860")
    print("Then open: http://localhost:8089")