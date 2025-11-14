# Deprecated Code

This directory contains deprecated code that has been replaced by newer implementations.

## Files

### ingestion.py
**Deprecated:** November 2025  
**Reason:** Replaced by service-based data ingestion (NVD, CISA KEV services)  
**Replacement:** Use `services/nvd_complete_service.py` and `services/cisa_kev_service.py`

The old NDJSON-based ingestion has been replaced with direct API integration:
- NVD data is fetched directly from the NVD API
- CISA KEV data is fetched from the CISA catalog
- No manual NDJSON file processing needed

**Note:** This file is kept for reference only. Do not use in production.
