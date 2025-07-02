#!/usr/bin/env python3
"""
Deployment Verification Script
Checks all dependencies and configurations before production deployment
"""

import os
import sys
import importlib
import json
from datetime import datetime

class DeploymentVerifier:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        
    def print_status(self, check_name: str, passed: bool, message: str = ""):
        """Print colored status for a check"""
        if passed:
            print(f"✅ {check_name}: PASSED {message}")
            self.checks_passed += 1
        else:
            print(f"❌ {check_name}: FAILED {message}")
            self.checks_failed += 1
            
    def print_warning(self, message: str):
        """Print a warning message"""
        print(f"⚠️  WARNING: {message}")
        self.warnings.append(message)
        
    def check_python_version(self):
        """Verify Python version is 3.8+"""
        version = sys.version_info
        passed = version.major == 3 and version.minor >= 8
        self.print_status(
            "Python Version",
            passed,
            f"(Python {version.major}.{version.minor}.{version.micro})"
        )
        
    def check_required_packages(self):
        """Verify all required packages are installed"""
        required_packages = [
            "gradio",
            "openai",
            "pydantic",
            "aiohttp",
            "python-dotenv",
            "sendgrid",
            "langsmith",
            "asyncio"
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                self.print_status(f"Package: {package}", True)
            except ImportError:
                self.print_status(f"Package: {package}", False)
                
    def check_environment_variables(self):
        """Verify critical environment variables"""
        env_vars = {
            "OPENAI_API_KEY": (True, "Required for AI agents"),
            "SERPER_API_KEY": (True, "Required for web search"),
            "SENDGRID_API_KEY": (False, "Optional for email delivery"),
            "LANGSMITH_API_KEY": (False, "Optional for tracing"),
            "USE_NEW_ARCHITECTURE": (False, "Controls architecture selection"),
            "SHADOW_MODE_PERCENTAGE": (False, "Controls A/B testing")
        }
        
        print("\n=== Environment Variables ===")
        for var, (required, description) in env_vars.items():
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "KEY" in var:
                    masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                else:
                    masked_value = value
                self.print_status(f"{var}", True, f"({masked_value}) - {description}")
            elif required:
                self.print_status(f"{var}", False, f"- {description}")
            else:
                self.print_warning(f"{var} not set - {description}")
                
    def check_file_structure(self):
        """Verify all critical files exist"""
        critical_files = [
            "deep_research.py",
            "research_manager_adapter.py",
            "research_manager.py",
            "integrated_research_manager.py",
            "manager_agent.py",
            "agent_tools.py",
            "performance_optimizer.py",
            "cache_manager.py",
            "error_handler.py"
        ]
        
        print("\n=== File Structure ===")
        for file in critical_files:
            exists = os.path.exists(file)
            self.print_status(f"File: {file}", exists)
            
    def check_permissions(self):
        """Verify directory permissions"""
        print("\n=== Directory Permissions ===")
        
        # Check if we can create performance data directory
        perf_dir = os.getenv("PERFORMANCE_DATA_DIR", "./performance_data")
        try:
            os.makedirs(perf_dir, exist_ok=True)
            test_file = os.path.join(perf_dir, "test_write.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self.print_status("Performance data directory", True, f"({perf_dir})")
        except Exception as e:
            self.print_status("Performance data directory", False, f"- {str(e)}")
            
        # Check cache directory
        cache_dir = "./cache"
        try:
            os.makedirs(cache_dir, exist_ok=True)
            self.print_status("Cache directory", True, f"({cache_dir})")
        except Exception as e:
            self.print_status("Cache directory", False, f"- {str(e)}")
            
    def check_configuration(self):
        """Verify configuration settings"""
        print("\n=== Configuration Settings ===")
        
        # Check deployment configuration
        use_new = os.getenv("USE_NEW_ARCHITECTURE", "false").lower() == "true"
        shadow_pct = float(os.getenv("SHADOW_MODE_PERCENTAGE", "0.1"))
        ui_toggle = os.getenv("UI_TOGGLE_ENABLED", "false").lower() == "true"
        
        self.print_status("Architecture", True, 
                         f"({'NEW' if use_new else 'OLD'} architecture active)")
        self.print_status("Shadow Mode", True, 
                         f"({shadow_pct*100:.0f}% of queries)")
        self.print_status("UI Toggle", True,
                         f"({'Enabled' if ui_toggle else 'Disabled'})")
        
        # Validate shadow mode percentage
        if shadow_pct < 0 or shadow_pct > 1:
            self.print_warning("Shadow mode percentage should be between 0 and 1")
            
    def run_import_tests(self):
        """Test importing all modules"""
        print("\n=== Import Tests ===")
        
        modules = [
            "research_manager_adapter",
            "performance_optimizer",
            "cache_manager",
            "error_handler",
            "agent_tools"
        ]
        
        for module in modules:
            try:
                importlib.import_module(module)
                self.print_status(f"Import: {module}", True)
            except Exception as e:
                self.print_status(f"Import: {module}", False, f"- {str(e)}")
                
    def generate_report(self):
        """Generate deployment readiness report"""
        print("\n" + "="*60)
        print("DEPLOYMENT READINESS REPORT")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Checks: {self.checks_passed + self.checks_failed}")
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.checks_failed == 0:
            print("\n🎉 DEPLOYMENT READY: All checks passed!")
            if self.warnings:
                print("   Please review warnings above before proceeding.")
        else:
            print("\n❌ NOT READY: Please fix failed checks before deployment.")
            
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "ready": self.checks_failed == 0
        }
        
        with open("deployment_verification.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: deployment_verification.json")
        
    def run_all_checks(self):
        """Run all deployment verification checks"""
        print("🚀 Deep Research Deployment Verification")
        print("="*60)
        
        print("\n=== System Requirements ===")
        self.check_python_version()
        self.check_required_packages()
        
        self.check_environment_variables()
        self.check_file_structure()
        self.check_permissions()
        self.check_configuration()
        self.run_import_tests()
        
        self.generate_report()
        
        return self.checks_failed == 0

if __name__ == "__main__":
    verifier = DeploymentVerifier()
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)