#!/bin/bash
# Enable beta feature for 5% of users

echo "🚀 Enabling Beta Feature: Intelligent Manager Architecture"
echo "=============================================="

# Enable the feature with 5% rollout
python beta_feature_manager.py enable new_architecture_toggle --percentage 5.0

echo ""
echo "✅ Beta feature enabled with 5% rollout"
echo ""
echo "To increase rollout percentage:"
echo "  python beta_feature_manager.py update new_architecture_toggle 10"
echo ""
echo "To whitelist specific users:"
echo "  python beta_feature_manager.py whitelist new_architecture_toggle user1 user2"
echo ""
echo "To check current status:"
echo "  python beta_feature_manager.py report"
echo ""