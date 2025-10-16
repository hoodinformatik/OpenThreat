# LLM Integration - Plain-Language CVE Summaries

OpenThreat uses a local LLM to generate user-friendly titles and descriptions for CVEs, making threat intelligence accessible to non-technical users.

## 🎯 What It Does

The LLM processes technical CVE data and generates:

1. **Simple Title** (< 10 words)
   - Describes the vulnerability in plain language
   - Includes affected vendor/product
   - Example: "Security Flaw in Microsoft Windows Allows Remote Access"

2. **Simple Description** (2-3 sentences)
   - Explains what the vulnerability is
   - Describes potential impact
   - No technical jargon
   - Example: "This vulnerability allows attackers to remotely access Windows systems without authentication. It affects all Windows 10 and 11 versions. Microsoft has released a security update to fix this issue."

## 🚀 Setup

### 1. Install Ollama

**Windows:**
```powershell
# Download from https://ollama.ai/download
# Or use winget:
winget install Ollama.Ollama
```

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Pull a Model

We recommend **Llama 3.2 3B** (fast, efficient, good quality):

```bash
ollama pull llama3.2:3b
```

**Alternative models:**
- `mistral:7b` - Larger, higher quality
- `llama3.2:1b` - Smaller, faster
- `phi3:mini` - Microsoft's efficient model

### 3. Install Python Dependencies

```bash
pip install ollama
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### 4. Run Database Migration

```bash
alembic upgrade head
```

## 📝 Usage

### Process All Unprocessed CVEs

```bash
python scripts/process_with_llm.py --all
```

### Process Specific CVE

```bash
python scripts/process_with_llm.py --cve CVE-2024-1234
```

### Process Limited Number

```bash
python scripts/process_with_llm.py --limit 10
```

### Reprocess All CVEs

```bash
python scripts/process_with_llm.py --reprocess
```

### Use Different Model

```bash
python scripts/process_with_llm.py --all --model mistral:7b
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```env
# LLM Configuration
LLM_ENABLED=true
LLM_MODEL=llama3.2:3b
OLLAMA_HOST=http://localhost:11434
```

### Disable LLM

If you don't want to use LLM features:

```env
LLM_ENABLED=false
```

The system will fall back to original CVE titles and descriptions.

## 📊 Performance

### Processing Speed

- **Llama 3.2 3B**: ~5-10 seconds per CVE
- **Mistral 7B**: ~10-20 seconds per CVE
- **Llama 3.2 1B**: ~3-5 seconds per CVE

### Batch Processing

For 3,209 CVEs with Llama 3.2 3B:
- **Estimated time**: 4-9 hours
- **Recommendation**: Run overnight or in batches

```bash
# Process 100 at a time
python scripts/process_with_llm.py --limit 100
```

## 🎨 Frontend Integration

The frontend automatically displays LLM-generated content when available:

```typescript
// Falls back to original title if simple_title is not available
const displayTitle = vuln.simple_title || vuln.title;
const displayDesc = vuln.simple_description || vuln.description;
```

## 🔄 Celery Integration (Optional)

Add LLM processing to automated updates:

```python
# backend/tasks.py
@celery_app.task(name="process_new_cves_with_llm")
def process_new_cves_with_llm():
    """Process newly added CVEs with LLM."""
    from backend.database import SessionLocal
    from backend.models import Vulnerability
    from backend.llm_service import get_llm_service
    
    session = SessionLocal()
    llm = get_llm_service()
    
    # Get unprocessed CVEs
    vulns = session.query(Vulnerability).filter(
        Vulnerability.llm_processed == False
    ).limit(10).all()  # Process 10 at a time
    
    for vuln in vulns:
        summary = llm.generate_cve_summary(...)
        vuln.simple_title = summary['simple_title']
        vuln.simple_description = summary['simple_description']
        vuln.llm_processed = True
        
    session.commit()
    session.close()
```

## 🐛 Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve
```

### Model Not Found

```bash
# List available models
ollama list

# Pull the model
ollama pull llama3.2:3b
```

### Slow Processing

- Use a smaller model (`llama3.2:1b`)
- Process in smaller batches
- Use GPU acceleration if available

### Out of Memory

- Use a smaller model
- Reduce batch size
- Close other applications

## 📈 Quality Examples

### Before (Technical)
**Title:** CVE-2024-1234: Improper Input Validation in Microsoft Windows SMB Server  
**Description:** A remote code execution vulnerability exists in the way that the Microsoft Server Message Block 3.1.1 (SMBv3) protocol handles certain requests. An attacker who successfully exploited the vulnerability could gain the ability to execute code on the target server or client...

### After (LLM-Generated)
**Simple Title:** Remote Access Flaw in Windows File Sharing  
**Simple Description:** This security issue allows hackers to take control of Windows computers through the file sharing feature. It affects Windows 10 and 11 systems. Microsoft has released an update to fix this problem, and users should install it immediately.

## 🔒 Privacy & Security

- **100% Local**: All LLM processing happens on your machine
- **No Data Sent**: No CVE data is sent to external services
- **Open Source**: Uses open-source models (Llama, Mistral)
- **Offline Capable**: Works without internet connection

## 📚 Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Llama 3.2 Model Card](https://ollama.ai/library/llama3.2)
- [Mistral Model Card](https://ollama.ai/library/mistral)

## 🎯 Roadmap

- [ ] Automatic LLM processing in Celery tasks
- [ ] Multi-language support (German, Spanish, French)
- [ ] Action recommendations generation
- [ ] Severity explanations
- [ ] Impact analysis
