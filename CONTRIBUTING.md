# Contributing to OpenThreat

Thank you for your interest in contributing to OpenThreat! This document provides guidelines and instructions for contributing.

## 🎯 Project Mission

OpenThreat aims to democratize threat intelligence by providing a free, open-source platform for tracking vulnerabilities and security threats.

## 📋 Ways to Contribute

### 1. Report Bugs
- Use GitHub Issues
- Include detailed reproduction steps
- Provide system information
- Include relevant logs

### 2. Suggest Features
- Open a GitHub Issue with the `enhancement` label
- Describe the use case
- Explain the expected behavior

### 3. Submit Code
- Fork the repository
- Create a feature branch
- Make your changes
- Submit a Pull Request

### 4. Improve Documentation
- Fix typos
- Add examples
- Clarify instructions
- Translate documentation

## 🔧 Development Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- Docker Desktop
- Git

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/hoodinformatik/OpenThreat.git
cd OpenThreat
```

2. **Start infrastructure**
```bash
docker-compose up -d postgres redis
```

3. **Backend setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

4. **Frontend setup**
```bash
cd frontend
npm install
npm run dev
```

5. **Access the application**
- Frontend: http://localhost:3000
- API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 📝 Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints
- Write docstrings for functions
- Maximum line length: 100 characters

```python
def fetch_vulnerabilities(limit: int = 100) -> List[Vulnerability]:
    """
    Fetch vulnerabilities from the database.
    
    Args:
        limit: Maximum number of vulnerabilities to fetch
        
    Returns:
        List of Vulnerability objects
    """
    pass
```

### TypeScript (Frontend)
- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Use meaningful variable names

```typescript
interface VulnerabilityProps {
  cveId: string;
  severity: string;
}

export function VulnerabilityCard({ cveId, severity }: VulnerabilityProps) {
  // Component logic
}
```

## 🧪 Testing

### Backend Tests
```bash
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📦 Pull Request Process

1. **Update your fork**
```bash
git checkout main
git pull upstream main
```

2. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

3. **Make your changes**
- Write clean, documented code
- Add tests if applicable
- Update documentation

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add new feature"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build/tooling changes

5. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

6. **Open a Pull Request**
- Go to GitHub
- Click "New Pull Request"
- Describe your changes
- Link related issues

## ✅ Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts
- [ ] PR description is clear

## 🚫 What NOT to Contribute

### Data Sources
- **Only public, legal data sources**
- No proprietary data
- No leaked data
- No personal information (PII)
- No illegal content

### Code
- No malicious code
- No backdoors
- No hardcoded credentials
- No copyright violations

## 📧 Questions?

- **Email:** hoodinformatik@gmail.com
- **GitHub Issues:** For bugs and features
- **GitHub Discussions:** For questions and ideas

## 📜 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for contributing to OpenThreat!** 🎉
