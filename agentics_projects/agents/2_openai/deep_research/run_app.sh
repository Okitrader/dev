#!/bin/bash
echo "Starting Deep Research System..."
echo "==================="
echo ""
cd /workspaces/dev/agentics_projects/agents/2_openai/deep_research
python deep_research.py 2>&1 | tee app.log