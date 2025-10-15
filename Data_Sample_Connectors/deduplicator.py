"""
Deduplication utility for CVE data from multiple sources.

This module provides functions to deduplicate CVE records from different sources
(NVD, EU CVE Search, CISA KEV) by merging data based on CVE ID.

Strategy:
1. Group all records by CVE ID
2. For each CVE ID, merge data from all sources
3. Prioritize data quality: CISA > NVD > EU CVE Search
4. Combine unique values (references, products, etc.)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict


def load_ndjson(path: Path) -> List[Dict[str, Any]]:
    """Load NDJSON file into list of dictionaries."""
    items = []
    if not path.exists():
        return items
    
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    
    return items


def merge_cve_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple CVE records for the same CVE ID.
    
    Priority order for data sources:
    1. CISA KEV (most authoritative for exploited vulns)
    2. NVD CVE (comprehensive official data)
    3. NVD Recent (recent updates)
    4. EU CVE Search (alternative metadata)
    
    Args:
        records: List of CVE records with the same CVE ID
    
    Returns:
        Merged CVE record
    """
    if not records:
        return {}
    
    if len(records) == 1:
        return records[0]
    
    # Sort by source priority
    source_priority = {
        "cisa": 1,
        "nvd_cve": 2,
        "nvd": 3,
        "eu_cve_search": 4,
    }
    
    records = sorted(records, key=lambda r: source_priority.get(r.get("source", ""), 99))
    
    # Start with the highest priority record
    merged = records[0].copy()
    
    # Track all sources
    sources = [r.get("source") for r in records if r.get("source")]
    merged["sources"] = list(set(sources))
    
    # Merge fields from other records
    for record in records[1:]:
        # Use non-null values from higher priority sources
        for key in ["description", "cvss_score", "cvss_vector", "severity"]:
            if not merged.get(key) and record.get(key):
                merged[key] = record[key]
        
        # Use latest timestamps
        for key in ["published", "last_modified"]:
            if record.get(key):
                if not merged.get(key) or record[key] > merged[key]:
                    merged[key] = record[key]
        
        # Combine lists (deduplicate)
        for key in ["vendors", "products", "affected_products", "cwe_ids"]:
            if record.get(key):
                existing_list = merged.get(key, [])
                new_list = record[key]
                
                # Ensure both are lists
                if not isinstance(existing_list, list):
                    existing_list = [existing_list] if existing_list else []
                if not isinstance(new_list, list):
                    new_list = [new_list] if new_list else []
                
                # Convert to strings and deduplicate
                existing = set(str(x) for x in existing_list if x)
                new_items = set(str(x) for x in new_list if x)
                merged[key] = sorted(existing | new_items)
        
        # Merge references (deduplicate by URL)
        if record.get("references"):
            existing_refs = {}
            # Handle existing references
            for r in merged.get("references", []):
                if isinstance(r, dict):
                    url = r.get("url")
                    if url:
                        existing_refs[url] = r
                elif isinstance(r, str):
                    existing_refs[r] = {"url": r, "type": "other"}
            
            # Add new references
            for ref in record["references"]:
                if isinstance(ref, dict):
                    url = ref.get("url")
                    if url and url not in existing_refs:
                        existing_refs[url] = ref
                elif isinstance(ref, str):
                    if ref not in existing_refs:
                        existing_refs[ref] = {"url": ref, "type": "other"}
            
            merged["references"] = list(existing_refs.values())
        
        # Exploited flag: True if any source says True
        if record.get("exploited_in_the_wild"):
            merged["exploited_in_the_wild"] = True
        
        # Keep CISA due date if present
        if not merged.get("cisa_due_date") and record.get("cisa_due_date"):
            merged["cisa_due_date"] = record["cisa_due_date"]
    
    return merged


def deduplicate_cves(cve_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate CVE records by CVE ID.
    
    Args:
        cve_records: List of CVE records from various sources
    
    Returns:
        List of deduplicated CVE records
    """
    # Group by CVE ID
    by_cve_id: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    for record in cve_records:
        cve_id = record.get("cve_id")
        if cve_id:
            by_cve_id[cve_id].append(record)
    
    # Merge records for each CVE ID
    deduplicated = []
    for cve_id, records in by_cve_id.items():
        merged = merge_cve_records(records)
        deduplicated.append(merged)
    
    # Sort by CVE ID
    deduplicated.sort(key=lambda r: r.get("cve_id", ""))
    
    return deduplicated


def deduplicate_files(input_files: List[Path], output_file: Path) -> int:
    """
    Deduplicate CVE records from multiple NDJSON files.
    
    Args:
        input_files: List of input NDJSON files
        output_file: Output NDJSON file for deduplicated records
    
    Returns:
        Number of deduplicated records written
    """
    # Load all records
    all_records = []
    for path in input_files:
        if path.exists():
            records = load_ndjson(path)
            print(f"Loaded {len(records)} records from {path.name}")
            all_records.extend(records)
    
    print(f"Total records before deduplication: {len(all_records)}")
    
    # Deduplicate
    deduplicated = deduplicate_cves(all_records)
    print(f"Total records after deduplication: {len(deduplicated)}")
    
    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        for record in deduplicated:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"Wrote {len(deduplicated)} deduplicated records to {output_file}")
    
    return len(deduplicated)


def get_latest_files(out_dir: Path, patterns: List[str]) -> List[Path]:
    """
    Get the latest file for each pattern.
    
    Args:
        out_dir: Output directory
        patterns: List of file name patterns (e.g., ["nvd_cve", "eu_cve"])
    
    Returns:
        List of latest files
    """
    latest_files = []
    
    for pattern in patterns:
        matching = sorted(out_dir.glob(f"{pattern}-*.ndjson"), reverse=True)
        if matching:
            latest_files.append(matching[0])
    
    return latest_files


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deduplicate CVE records from multiple sources")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).parent / "out",
        help="Input directory containing NDJSON files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "out" / "deduplicated_cves.ndjson",
        help="Output file for deduplicated records",
    )
    parser.add_argument(
        "--patterns",
        nargs="+",
        default=["cisa_kev", "nvd_cve", "nvd_recent", "eu_cve"],
        help="File name patterns to include",
    )
    
    args = parser.parse_args()
    
    # Get latest files for each pattern
    input_files = get_latest_files(args.input_dir, args.patterns)
    
    if not input_files:
        print("No input files found!")
        exit(1)
    
    print(f"Input files: {[f.name for f in input_files]}")
    
    # Deduplicate
    count = deduplicate_files(input_files, args.output)
    
    print(f"\nDeduplication complete: {count} unique CVEs")
