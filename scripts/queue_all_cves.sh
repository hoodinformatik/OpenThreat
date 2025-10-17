#!/bin/bash
# Queue all CVEs for LLM processing

echo "═══════════════════════════════════════════════════════════"
echo "  Queuing ALL CVEs for LLM Processing"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Get initial stats
echo "Initial stats:"
python3 scripts/start_llm_processing.py --stats
echo ""

# Calculate batches needed
TOTAL_PENDING=314246
BATCH_SIZE=1000
BATCHES=$((TOTAL_PENDING / BATCH_SIZE + 1))

echo "Queuing $TOTAL_PENDING CVEs in batches of $BATCH_SIZE"
echo "Estimated batches: $BATCHES"
echo ""
read -p "Press Enter to start or Ctrl+C to cancel..."
echo ""

# Counter
QUEUED=0

# Queue in batches
for i in $(seq 1 $BATCHES); do
    echo "[$i/$BATCHES] Queuing batch $i..."
    
    # Queue high priority first, then all
    if [ $i -le 30 ]; then
        python3 scripts/start_llm_processing.py --batch-size $BATCH_SIZE --priority high
    else
        python3 scripts/start_llm_processing.py --batch-size $BATCH_SIZE --priority all
    fi
    
    QUEUED=$((QUEUED + BATCH_SIZE))
    
    # Show progress every 10 batches
    if [ $((i % 10)) -eq 0 ]; then
        echo ""
        echo "Progress: ~$QUEUED CVEs queued"
        python3 scripts/start_llm_processing.py --stats
        echo ""
    fi
    
    # Small delay to not overwhelm Redis
    sleep 1
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  All CVEs queued for processing!"
echo "═══════════════════════════════════════════════════════════"
echo ""
python3 scripts/start_llm_processing.py --stats
