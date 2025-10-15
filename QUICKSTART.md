# OpenThreat - Quick Start Guide

## 🚀 Schnellstart (Alles auf einmal)

### Windows

**Option 1: Mit automatischen Updates (empfohlen)**

Doppelklick auf:
```
start-with-celery.bat
```

Das startet automatisch:
- ✅ Docker Container (PostgreSQL, Redis)
- ✅ Backend API (Port 8001)
- ✅ Frontend (Port 3000)
- ✅ Celery Worker (Background Tasks)
- ✅ Celery Beat (Automatische Updates alle 2h)

**Option 2: Ohne automatische Updates**

Doppelklick auf:
```
start.bat
```

Das startet nur:
- ✅ Docker Container (PostgreSQL, Redis)
- ✅ Backend API (Port 8001)
- ✅ Frontend (Port 3000)

Dann öffne im Browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/docs

### Stoppen

Doppelklick auf:
```
stop.bat
```

---

## 📝 Einzeln starten

### Nur Backend starten
```
start-backend.bat
```
Öffnet: http://localhost:8001/docs

### Nur Frontend starten
```
start-frontend.bat
```
Öffnet: http://localhost:3000

### Nur Celery Worker starten
```
start-celery-worker.bat
```
Verarbeitet Background Tasks

### Nur Celery Beat starten
```
start-celery-beat.bat
```
Plant automatische Updates

---

## 🔧 Manuell starten (falls Skripte nicht funktionieren)

### 1. Docker starten
```powershell
docker-compose up -d postgres redis
```

### 2. Backend starten
```powershell
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

### 3. Frontend starten (neues Terminal)
```powershell
cd frontend
npm run dev
```

---

## ⚙️ Erstmalige Einrichtung

Falls du das Projekt zum ersten Mal startest:

### 1. Dependencies installieren

**Python:**
```powershell
pip install -r requirements.txt
```

**Node.js:**
```powershell
cd frontend
npm install
cd ..
```

### 2. Datenbank einrichten
```powershell
# Docker starten
docker-compose up -d postgres redis

# Migrations ausführen
alembic upgrade head

# Daten sammeln
python Data_Sample_Connectors/run_all.py

# Daten laden
python -m backend.ingestion Data_Sample_Connectors/out/deduplicated_cves.ndjson initial_load
```

### 3. Jetzt kannst du `start.bat` verwenden! 🎉

---

## 🐛 Troubleshooting

### Docker startet nicht
- Docker Desktop öffnen und warten bis es läuft
- Dann `start.bat` erneut ausführen

### Port bereits belegt
**Backend (8001):**
```powershell
# Prozess finden und beenden
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

**Frontend (3000):**
```powershell
# Prozess finden und beenden
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Datenbank-Verbindung fehlgeschlagen
```powershell
# Docker Container neu starten
docker-compose restart postgres
```

### Frontend zeigt "fetch failed"
1. Prüfe ob Backend läuft: http://localhost:8001/health
2. Prüfe `frontend/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
   ```
3. Frontend neu starten

---

## 📊 URLs zum Merken

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8001/docs |
| API ReDoc | http://localhost:8001/redoc |
| API Health | http://localhost:8001/health |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## 🔄 Daten aktualisieren

### Automatisch (mit Celery)

Wenn Celery läuft, werden Daten automatisch alle 2 Stunden aktualisiert.

### Manuell triggern

**Via API:**
```powershell
curl -X POST http://localhost:8001/api/v1/tasks/update-vulnerabilities
```

**Via CLI:**
```powershell
python scripts/manage_tasks.py update
```

### Komplett manuell

```powershell
# Neue Daten sammeln
python Data_Sample_Connectors/run_all.py

# In Datenbank laden
python -m backend.ingestion Data_Sample_Connectors/out/deduplicated_cves.ndjson update
```

---

## 💡 Tipps

- **Logs anschauen**: Die Fenster mit Backend/Frontend zeigen Live-Logs
- **Neu laden**: Strg+C im Terminal und Skript erneut starten
- **Clean Start**: `stop.bat` ausführen, dann `start.bat`
- **Nur API testen**: `start-backend.bat` und http://localhost:8001/docs öffnen

---

## 🎯 Nächste Schritte

1. ✅ Öffne http://localhost:3000
2. ✅ Erkunde das Dashboard
3. ✅ Suche nach CVEs
4. ✅ Schaue dir Details an
5. ✅ Abonniere RSS Feeds

Viel Spaß! 🚀
