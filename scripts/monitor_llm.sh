#!/bin/bash
# LLM Processing Monitor

while true; do
    clear
    echo "═══════════════════════════════════════════════════════════"
    echo "  OpenThreat LLM Processing Monitor"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    # Get stats
    python3 scripts/start_llm_processing.py --stats
    
    echo ""
    echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Press Ctrl+C to exit"
    echo ""
    
    # Wait 10 seconds
    sleep 10
done
