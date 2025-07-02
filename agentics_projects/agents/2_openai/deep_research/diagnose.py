#!/usr/bin/env python3
"""Diagnostic script to check what's wrong"""

import subprocess
import requests
import time

print("🔍 DIAGNOSTIC CHECK FOR DEEP RESEARCH SYSTEM")
print("=" * 50)

# 1. Check if port 7860 is in use
print("\n1. Checking port 7860...")
try:
    result = subprocess.run(["lsof", "-i", ":7860"], capture_output=True, text=True)
    if result.stdout:
        print("✅ Port 7860 is in use")
        print(result.stdout)
    else:
        print("❌ Port 7860 is NOT in use")
except Exception as e:
    print(f"❌ Error checking port: {e}")

# 2. Try to connect to the app
print("\n2. Testing connection to http://localhost:7860...")
try:
    response = requests.get("http://localhost:7860", timeout=5)
    print(f"✅ Got response: Status {response.status_code}")
except requests.exceptions.ConnectionRefused:
    print("❌ Connection refused - app not running")
except requests.exceptions.Timeout:
    print("❌ Connection timed out")
except Exception as e:
    print(f"❌ Error: {e}")

# 3. Check Python processes
print("\n3. Checking Python processes...")
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
python_procs = [line for line in result.stdout.split("\n") if "python" in line and "deep_research" in line]
if python_procs:
    print("✅ Found deep_research process:")
    for proc in python_procs:
        print(f"   {proc[:100]}...")
else:
    print("❌ No deep_research process found")

# 4. Check environment variables
print("\n4. Checking environment...")
import os
required_vars = ["OPENAI_API_KEY", "SERPER_API_KEY"]
for var in required_vars:
    if os.getenv(var):
        print(f"✅ {var} is set")
    else:
        print(f"❌ {var} is NOT set")

# 5. Try importing the modules
print("\n5. Testing imports...")
try:
    import gradio
    print("✅ Gradio imported successfully")
except ImportError as e:
    print(f"❌ Gradio import failed: {e}")

try:
    from research_manager_adapter import ResearchManagerAdapter
    print("✅ ResearchManagerAdapter imported successfully")
except Exception as e:
    print(f"❌ ResearchManagerAdapter import failed: {e}")

print("\n" + "=" * 50)
print("Diagnosis complete. Check the results above.")