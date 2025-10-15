# 🤖 Quick Start: LLM Integration

Generate user-friendly CVE summaries with a local LLM in 5 minutes!

## Step 1: Install Ollama

### Windows
Download and install from: https://ollama.ai/download

Or use PowerShell:
```powershell
winget install Ollama.Ollama
```

### Linux/Mac
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## Step 2: Pull the Model

```bash
ollama pull llama3.2:3b
```

This downloads a 2GB model. Wait for it to complete.

## Step 3: Install Python Dependencies

```bash
pip install ollama
```

## Step 4: Run Database Migration

```bash
alembic upgrade head
```

This adds the new fields (`simple_title`, `simple_description`) to your database.

## Step 5: Process CVEs

### Test with 1 CVE
```bash
python scripts/process_with_llm.py --limit 1
```

### Process 10 CVEs
```bash
python scripts/process_with_llm.py --limit 10
```

### Process All Unprocessed CVEs
```bash
python scripts/process_with_llm.py --all
```

**Note:** Processing all 3,209 CVEs takes 4-9 hours. Run overnight!

## Example Output

```
🤖 Processing 1 CVEs with LLM...
   Model: llama3.2:3b

Processing CVE-2024-1234... ✅
  Title: Remote Access Flaw in Windows File Sharing
  Desc:  This security issue allows hackers to take control of Windows computers...

✅ Processed: 1
```

## Verify in Frontend

1. Start the application:
   ```bash
   start.bat
   ```

2. Open http://localhost:3000

3. Browse vulnerabilities - you'll see the simplified titles and descriptions!

## Troubleshooting

### "Ollama not available"
```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve
```

### "Model not found"
```bash
# Pull the model again
ollama pull llama3.2:3b
```

### Too Slow?
Use a smaller model:
```bash
ollama pull llama3.2:1b
python scripts/process_with_llm.py --all --model llama3.2:1b
```

## What's Next?

- Process more CVEs in batches
- Try different models (mistral, phi3)
- Integrate into Celery for automatic processing
- See `LLM.md` for full documentation

## Disable LLM

Don't want to use LLM? No problem!

The system automatically falls back to original CVE data if:
- Ollama is not installed
- Model is not available
- LLM processing fails

No configuration needed - it just works!
