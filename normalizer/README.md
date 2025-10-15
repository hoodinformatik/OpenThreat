
# Normalizer (NDJSON → Unified Models)

Ziel: Die NDJSON-Outputs aus `Data_Sample_Connectors/out` in ein einheitliches Schema überführen (ohne DB).
Ergebnis: `normalizer/out/vulnerabilities.ndjson` und `normalizer/out/techniques.ndjson`.

## Struktur
```
normalizer/
  mappers/
    models.py          # Vulnerability, Technique, IOC (Pydantic v2)
    cisa_mapper.py     # CISA NDJSON → Vulnerability
    nvd_mapper.py      # NVD NDJSON → Vulnerability
    mitre_mapper.py    # MITRE NDJSON → Technique
  runner.py            # liest neueste Sample-Dateien und schreibt normalisierte NDJSONs
  out/                 # Ergebnisse
```

## Nutzung
```bash
python normalizer/runner.py

# Ergebnisse prüfen
head -n 3 normalizer/out/vulnerabilities.ndjson
head -n 3 normalizer/out/techniques.ndjson
```
