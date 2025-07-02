"""
Beta Feature Manager for Deep Research System
Controls gradual rollout of new features to users
"""

import json
import os
import hashlib
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class BetaFeatureManager:
    """Manages beta feature rollout and user eligibility"""
    
    def __init__(self, config_file: str = "beta_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load beta configuration"""
        default_config = {
            "features": {
                "new_architecture_toggle": {
                    "enabled": False,
                    "rollout_percentage": 0,
                    "user_whitelist": [],
                    "user_blacklist": [],
                    "start_date": None,
                    "metrics": {
                        "total_eligible": 0,
                        "total_enabled": 0,
                        "total_used": 0
                    }
                }
            },
            "global_settings": {
                "beta_opt_in_required": False,
                "power_user_threshold": 10,  # Number of queries to be considered power user
                "rollout_strategy": "percentage"  # percentage, whitelist, or gradual
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Failed to load beta config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save beta configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save beta config: {e}")
    
    def _hash_user_id(self, user_id: str) -> int:
        """Generate consistent hash for user ID"""
        return int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    
    def is_user_eligible(self, feature: str, user_id: str, 
                        user_metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user is eligible for a beta feature"""
        
        if feature not in self.config["features"]:
            return False
        
        feature_config = self.config["features"][feature]
        
        # Check if feature is enabled
        if not feature_config["enabled"]:
            return False
        
        # Check blacklist first
        if user_id in feature_config["user_blacklist"]:
            return False
        
        # Check whitelist
        if user_id in feature_config["user_whitelist"]:
            return True
        
        # Check rollout strategy
        strategy = self.config["global_settings"]["rollout_strategy"]
        
        if strategy == "whitelist":
            # Only whitelisted users
            return False
        
        elif strategy == "percentage":
            # Deterministic percentage rollout
            rollout_pct = feature_config["rollout_percentage"]
            if rollout_pct <= 0:
                return False
            if rollout_pct >= 100:
                return True
            
            # Use hash for consistent assignment
            user_hash = self._hash_user_id(user_id)
            threshold = (rollout_pct / 100.0) * (2**32)
            return (user_hash % (2**32)) < threshold
        
        elif strategy == "gradual":
            # Check if user is a power user
            if user_metrics:
                query_count = user_metrics.get("total_queries", 0)
                power_threshold = self.config["global_settings"]["power_user_threshold"]
                
                if query_count >= power_threshold:
                    # Power users get features first
                    return self._check_percentage_rollout(
                        user_id, 
                        min(feature_config["rollout_percentage"] * 2, 100)
                    )
            
            # Regular users
            return self._check_percentage_rollout(
                user_id, 
                feature_config["rollout_percentage"]
            )
        
        return False
    
    def _check_percentage_rollout(self, user_id: str, percentage: float) -> bool:
        """Check if user falls within percentage rollout"""
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True
        
        user_hash = self._hash_user_id(user_id)
        threshold = (percentage / 100.0) * (2**32)
        return (user_hash % (2**32)) < threshold
    
    def record_feature_usage(self, feature: str, user_id: str, enabled: bool):
        """Record when a user uses a beta feature"""
        if feature not in self.config["features"]:
            return
        
        metrics = self.config["features"][feature]["metrics"]
        
        # Update metrics
        if enabled:
            metrics["total_enabled"] = metrics.get("total_enabled", 0) + 1
        
        metrics["total_used"] = metrics.get("total_used", 0) + 1
        
        # Save periodically (every 10 uses)
        if metrics["total_used"] % 10 == 0:
            self._save_config()
    
    def update_rollout_percentage(self, feature: str, percentage: float):
        """Update rollout percentage for a feature"""
        if feature not in self.config["features"]:
            logger.error(f"Unknown feature: {feature}")
            return
        
        old_pct = self.config["features"][feature]["rollout_percentage"]
        self.config["features"][feature]["rollout_percentage"] = percentage
        
        logger.info(f"Updated {feature} rollout: {old_pct}% -> {percentage}%")
        self._save_config()
    
    def enable_feature(self, feature: str, percentage: float = 5.0):
        """Enable a beta feature with initial rollout percentage"""
        if feature not in self.config["features"]:
            self.config["features"][feature] = {
                "enabled": True,
                "rollout_percentage": percentage,
                "user_whitelist": [],
                "user_blacklist": [],
                "start_date": datetime.now().isoformat(),
                "metrics": {
                    "total_eligible": 0,
                    "total_enabled": 0,
                    "total_used": 0
                }
            }
        else:
            self.config["features"][feature]["enabled"] = True
            self.config["features"][feature]["rollout_percentage"] = percentage
            if not self.config["features"][feature].get("start_date"):
                self.config["features"][feature]["start_date"] = datetime.now().isoformat()
        
        logger.info(f"Enabled feature {feature} with {percentage}% rollout")
        self._save_config()
    
    def add_to_whitelist(self, feature: str, user_ids: List[str]):
        """Add users to feature whitelist"""
        if feature not in self.config["features"]:
            logger.error(f"Unknown feature: {feature}")
            return
        
        whitelist = set(self.config["features"][feature]["user_whitelist"])
        whitelist.update(user_ids)
        self.config["features"][feature]["user_whitelist"] = list(whitelist)
        
        logger.info(f"Added {len(user_ids)} users to {feature} whitelist")
        self._save_config()
    
    def get_feature_metrics(self, feature: str) -> Dict[str, Any]:
        """Get metrics for a beta feature"""
        if feature not in self.config["features"]:
            return {}
        
        feature_config = self.config["features"][feature]
        metrics = feature_config["metrics"].copy()
        
        # Calculate adoption rate
        if metrics.get("total_used", 0) > 0:
            metrics["adoption_rate"] = (
                metrics.get("total_enabled", 0) / metrics.get("total_used", 0) * 100
            )
        else:
            metrics["adoption_rate"] = 0
        
        # Add configuration info
        metrics["enabled"] = feature_config["enabled"]
        metrics["rollout_percentage"] = feature_config["rollout_percentage"]
        metrics["start_date"] = feature_config.get("start_date")
        
        return metrics
    
    def generate_rollout_report(self) -> Dict[str, Any]:
        """Generate comprehensive rollout report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "global_settings": self.config["global_settings"],
            "features": {}
        }
        
        for feature, config in self.config["features"].items():
            metrics = self.get_feature_metrics(feature)
            report["features"][feature] = metrics
        
        return report

# Global instance
beta_manager = BetaFeatureManager()

def check_beta_eligibility(user_id: str, feature: str = "new_architecture_toggle",
                          user_metrics: Optional[Dict[str, Any]] = None) -> bool:
    """Check if user is eligible for beta feature"""
    return beta_manager.is_user_eligible(feature, user_id, user_metrics)

def record_beta_usage(user_id: str, feature: str, enabled: bool):
    """Record beta feature usage"""
    beta_manager.record_feature_usage(feature, user_id, enabled)

# CLI for managing beta features
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage beta features")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Enable feature
    enable_parser = subparsers.add_parser("enable", help="Enable a beta feature")
    enable_parser.add_argument("feature", help="Feature name")
    enable_parser.add_argument("--percentage", type=float, default=5.0,
                              help="Initial rollout percentage")
    
    # Update rollout
    update_parser = subparsers.add_parser("update", help="Update rollout percentage")
    update_parser.add_argument("feature", help="Feature name")
    update_parser.add_argument("percentage", type=float, help="New percentage")
    
    # Whitelist users
    whitelist_parser = subparsers.add_parser("whitelist", help="Add users to whitelist")
    whitelist_parser.add_argument("feature", help="Feature name")
    whitelist_parser.add_argument("users", nargs="+", help="User IDs to whitelist")
    
    # Report
    report_parser = subparsers.add_parser("report", help="Generate rollout report")
    
    # Check user
    check_parser = subparsers.add_parser("check", help="Check user eligibility")
    check_parser.add_argument("user_id", help="User ID to check")
    check_parser.add_argument("--feature", default="new_architecture_toggle",
                             help="Feature to check")
    
    args = parser.parse_args()
    
    if args.command == "enable":
        beta_manager.enable_feature(args.feature, args.percentage)
        print(f"Enabled {args.feature} with {args.percentage}% rollout")
    
    elif args.command == "update":
        beta_manager.update_rollout_percentage(args.feature, args.percentage)
        print(f"Updated {args.feature} to {args.percentage}% rollout")
    
    elif args.command == "whitelist":
        beta_manager.add_to_whitelist(args.feature, args.users)
        print(f"Added {len(args.users)} users to {args.feature} whitelist")
    
    elif args.command == "report":
        report = beta_manager.generate_rollout_report()
        print(json.dumps(report, indent=2))
    
    elif args.command == "check":
        eligible = beta_manager.is_user_eligible(args.feature, args.user_id)
        print(f"User {args.user_id} is {'eligible' if eligible else 'not eligible'} for {args.feature}")
    
    else:
        parser.print_help()