
from pathlib import Path
from importlib import import_module

CONNECTORS = [
    ("cisa_kev", "cisa_kev"),
    ("nvd_recent", "nvd_recent"),
    ("nvd_cve", "nvd_cve"),  # Comprehensive CVE data from NVD
    ("eu_cve", "eu_cve"),    # European CVE data from CVE Search
    #("urlhaus_recent", "urlhaus_recent"), --> some fixing to do here as URL Haus seems to act kinda strange
    ("mitre_attack_enterprise", "mitre_attack_enterprise"),
]


def main():
    base = Path(__file__).parent
    out = base / "out"
    out.mkdir(exist_ok=True)
    
    # Run all connectors
    output_files = []
    for title, mod_name in CONNECTORS:
        print(f"==> Running {title}")
        try:
            mod = import_module(mod_name)
            path = mod.run(out)
            print(f"    Wrote {path}")
            output_files.append(path)
        except Exception as e:
            print(f"    ERROR: {e}")
    
    # Run deduplication
    print("\n==> Running deduplication")
    try:
        from deduplicator import deduplicate_files, get_latest_files
        
        # Get latest files for CVE sources
        cve_patterns = ["cisa_kev", "nvd_cve", "nvd_recent", "eu_cve"]
        latest_files = get_latest_files(out, cve_patterns)
        
        if latest_files:
            dedup_output = out / "deduplicated_cves.ndjson"
            count = deduplicate_files(latest_files, dedup_output)
            print(f"    Deduplicated {count} unique CVEs to {dedup_output}")
    except Exception as e:
        print(f"    ERROR during deduplication: {e}")


if __name__ == "__main__":
    main()
