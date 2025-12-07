"""
Tech Stack Service for parsing dependency files and matching CVEs.

Supports:
- JavaScript: package.json, package-lock.json
- Python: requirements.txt, Pipfile, pyproject.toml
- Ruby: Gemfile
- PHP: composer.json
- Java: pom.xml
- Go: go.mod
- Rust: Cargo.toml
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.models import PackageCPEMapping, TechStack, TechStackMatch, Vulnerability

logger = logging.getLogger(__name__)


# Common package name to CPE mappings for popular packages
# This helps with accurate matching since package names don't always match CPE products
KNOWN_MAPPINGS = {
    "npm": {
        "express": ("expressjs", "express"),
        "lodash": ("lodash", "lodash"),
        "axios": ("axios", "axios"),
        "react": ("facebook", "react"),
        "react-dom": ("facebook", "react"),
        "vue": ("vuejs", "vue"),
        "angular": ("angular", "angular"),
        "jquery": ("jquery", "jquery"),
        "moment": ("momentjs", "moment"),
        "webpack": ("webpack", "webpack"),
        "next": ("vercel", "next.js"),
        "typescript": ("microsoft", "typescript"),
        "node-fetch": ("node-fetch", "node-fetch"),
        "minimist": ("minimist", "minimist"),
        "ws": ("ws_project", "ws"),
        "jsonwebtoken": ("auth0", "jsonwebtoken"),
        "helmet": ("helmetjs", "helmet"),
        "cors": ("expressjs", "cors"),
        "dotenv": ("dotenv", "dotenv"),
        "mongoose": ("mongoosejs", "mongoose"),
        "sequelize": ("sequelize", "sequelize"),
        "prisma": ("prisma", "prisma"),
        "bcrypt": ("bcrypt", "bcrypt"),
        "uuid": ("uuid", "uuid"),
        "chalk": ("chalk", "chalk"),
        "commander": ("commander", "commander"),
        "yargs": ("yargs", "yargs"),
        "debug": ("debug", "debug"),
        "async": ("async", "async"),
        "bluebird": ("bluebird", "bluebird"),
        "request": ("request", "request"),
        "superagent": ("superagent", "superagent"),
        "cheerio": ("cheerio", "cheerio"),
        "puppeteer": ("puppeteer", "puppeteer"),
        "socket.io": ("socket", "socket.io"),
        "redis": ("redis", "node_redis"),
        "pg": ("postgresql", "node-postgres"),
        "mysql": ("mysql", "mysql"),
        "mysql2": ("mysql", "mysql2"),
        "mongodb": ("mongodb", "mongodb"),
    },
    "pypi": {
        "django": ("djangoproject", "django"),
        "flask": ("palletsprojects", "flask"),
        "fastapi": ("fastapi", "fastapi"),
        "requests": ("python-requests", "requests"),
        "numpy": ("numpy", "numpy"),
        "pandas": ("pandas-dev", "pandas"),
        "pillow": ("python-pillow", "pillow"),
        "sqlalchemy": ("sqlalchemy", "sqlalchemy"),
        "celery": ("celeryproject", "celery"),
        "redis": ("redis", "redis-py"),
        "psycopg2": ("psycopg", "psycopg2"),
        "boto3": ("amazon", "boto3"),
        "pyyaml": ("pyyaml", "pyyaml"),
        "jinja2": ("palletsprojects", "jinja2"),
        "cryptography": ("cryptography", "cryptography"),
        "paramiko": ("paramiko", "paramiko"),
        "urllib3": ("urllib3", "urllib3"),
        "certifi": ("certifi", "certifi"),
        "aiohttp": ("aiohttp", "aiohttp"),
        "httpx": ("encode", "httpx"),
        "pydantic": ("pydantic", "pydantic"),
        "uvicorn": ("encode", "uvicorn"),
        "gunicorn": ("gunicorn", "gunicorn"),
        "werkzeug": ("palletsprojects", "werkzeug"),
        "beautifulsoup4": ("crummy", "beautifulsoup"),
        "lxml": ("lxml", "lxml"),
        "scrapy": ("scrapy", "scrapy"),
        "selenium": ("selenium", "selenium"),
        "pytest": ("pytest", "pytest"),
        "tensorflow": ("google", "tensorflow"),
        "torch": ("pytorch", "pytorch"),
        "scikit-learn": ("scikit-learn", "scikit-learn"),
    },
    "rubygems": {
        "rails": ("rubyonrails", "rails"),
        "rack": ("rack", "rack"),
        "sinatra": ("sinatra", "sinatra"),
        "nokogiri": ("nokogiri", "nokogiri"),
        "devise": ("heartcombo", "devise"),
        "puma": ("puma", "puma"),
        "sidekiq": ("sidekiq", "sidekiq"),
        "redis": ("redis", "redis-rb"),
        "pg": ("postgresql", "pg"),
        "mysql2": ("mysql", "mysql2"),
    },
    "packagist": {
        "laravel/framework": ("laravel", "laravel"),
        "symfony/symfony": ("symfony", "symfony"),
        "guzzlehttp/guzzle": ("guzzle", "guzzle"),
        "monolog/monolog": ("monolog", "monolog"),
        "doctrine/orm": ("doctrine", "orm"),
        "phpunit/phpunit": ("phpunit", "phpunit"),
    },
    "maven": {
        "org.springframework:spring-core": ("vmware", "spring_framework"),
        "org.springframework.boot:spring-boot": ("vmware", "spring_boot"),
        "log4j:log4j": ("apache", "log4j"),
        "org.apache.logging.log4j:log4j-core": ("apache", "log4j"),
        "com.fasterxml.jackson.core:jackson-databind": (
            "fasterxml",
            "jackson-databind",
        ),
        "org.apache.struts:struts2-core": ("apache", "struts"),
        "org.apache.tomcat:tomcat": ("apache", "tomcat"),
    },
    "go": {
        "github.com/gin-gonic/gin": ("gin-gonic", "gin"),
        "github.com/gorilla/mux": ("gorilla", "mux"),
        "github.com/go-redis/redis": ("go-redis", "redis"),
        "github.com/jackc/pgx": ("jackc", "pgx"),
        "github.com/sirupsen/logrus": ("sirupsen", "logrus"),
    },
    "cargo": {
        "serde": ("serde", "serde"),
        "tokio": ("tokio", "tokio"),
        "actix-web": ("actix", "actix-web"),
        "reqwest": ("reqwest", "reqwest"),
        "hyper": ("hyperium", "hyper"),
    },
}


class TechStackService:
    """Service for parsing tech stacks and matching CVEs."""

    def parse_file(
        self, content: str, filename: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Parse a dependency file and extract packages.

        Args:
            content: File content as string
            filename: Original filename to determine parser

        Returns:
            Tuple of (list of packages, ecosystem)
        """
        filename_lower = filename.lower()

        if filename_lower == "package.json":
            return self._parse_package_json(content), "npm"
        elif filename_lower == "package-lock.json":
            return self._parse_package_lock_json(content), "npm"
        elif filename_lower == "requirements.txt":
            return self._parse_requirements_txt(content), "pypi"
        elif filename_lower == "pipfile":
            return self._parse_pipfile(content), "pypi"
        elif filename_lower == "pyproject.toml":
            return self._parse_pyproject_toml(content), "pypi"
        elif filename_lower == "gemfile":
            return self._parse_gemfile(content), "rubygems"
        elif filename_lower == "gemfile.lock":
            return self._parse_gemfile_lock(content), "rubygems"
        elif filename_lower == "composer.json":
            return self._parse_composer_json(content), "packagist"
        elif filename_lower == "pom.xml":
            return self._parse_pom_xml(content), "maven"
        elif filename_lower == "go.mod":
            return self._parse_go_mod(content), "go"
        elif filename_lower == "cargo.toml":
            return self._parse_cargo_toml(content), "cargo"
        else:
            raise ValueError(f"Unsupported file type: {filename}")

    def _parse_package_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse package.json file."""
        packages = []
        try:
            data = json.loads(content)

            # Parse dependencies
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    # Clean version string
                    version = self._clean_version(version)
                    packages.append(
                        {
                            "name": name,
                            "version": version,
                            "ecosystem": "npm",
                            "dev": dep_type == "devDependencies",
                        }
                    )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse package.json: {e}")

        return packages

    def _parse_package_lock_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse package-lock.json file."""
        packages = []
        try:
            data = json.loads(content)

            # Handle npm v7+ lockfile format
            if "packages" in data:
                for path, info in data["packages"].items():
                    if path and not path.startswith("node_modules/"):
                        continue
                    name = (
                        path.replace("node_modules/", "")
                        if path
                        else data.get("name", "")
                    )
                    if name and "version" in info:
                        packages.append(
                            {
                                "name": name,
                                "version": info["version"],
                                "ecosystem": "npm",
                                "dev": info.get("dev", False),
                            }
                        )

            # Handle older lockfile format
            elif "dependencies" in data:
                for name, info in data["dependencies"].items():
                    if "version" in info:
                        packages.append(
                            {
                                "name": name,
                                "version": info["version"],
                                "ecosystem": "npm",
                                "dev": info.get("dev", False),
                            }
                        )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse package-lock.json: {e}")

        return packages

    def _parse_requirements_txt(self, content: str) -> List[Dict[str, Any]]:
        """Parse requirements.txt file."""
        packages = []

        for line in content.split("\n"):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Handle various formats: package==1.0.0, package>=1.0.0, package[extra]==1.0.0
            match = re.match(r"^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?(?:[=<>!~]+(.+))?", line)
            if match:
                name = match.group(1).lower()
                version = match.group(2) if match.group(2) else None
                packages.append(
                    {
                        "name": name,
                        "version": version,
                        "ecosystem": "pypi",
                    }
                )

        return packages

    def _parse_pipfile(self, content: str) -> List[Dict[str, Any]]:
        """Parse Pipfile (TOML format)."""
        packages = []

        try:
            import tomllib

            data = tomllib.loads(content)

            for section in ["packages", "dev-packages"]:
                deps = data.get(section, {})
                for name, spec in deps.items():
                    version = None
                    if isinstance(spec, str) and spec != "*":
                        version = self._clean_version(spec)
                    elif isinstance(spec, dict):
                        version = spec.get("version")

                    packages.append(
                        {
                            "name": name.lower(),
                            "version": version,
                            "ecosystem": "pypi",
                            "dev": section == "dev-packages",
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to parse Pipfile: {e}")

        return packages

    def _parse_pyproject_toml(self, content: str) -> List[Dict[str, Any]]:
        """Parse pyproject.toml file."""
        packages = []

        try:
            import tomllib

            data = tomllib.loads(content)

            # Poetry format
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                for section in ["dependencies", "dev-dependencies"]:
                    deps = poetry.get(section, {})
                    for name, spec in deps.items():
                        if name == "python":
                            continue
                        version = None
                        if isinstance(spec, str):
                            version = self._clean_version(spec)
                        elif isinstance(spec, dict):
                            version = spec.get("version")

                        packages.append(
                            {
                                "name": name.lower(),
                                "version": version,
                                "ecosystem": "pypi",
                                "dev": section == "dev-dependencies",
                            }
                        )

            # PEP 621 format
            if "project" in data:
                deps = data["project"].get("dependencies", [])
                for dep in deps:
                    match = re.match(
                        r"^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?(?:[=<>!~]+(.+))?", dep
                    )
                    if match:
                        packages.append(
                            {
                                "name": match.group(1).lower(),
                                "version": match.group(2),
                                "ecosystem": "pypi",
                            }
                        )

        except Exception as e:
            logger.error(f"Failed to parse pyproject.toml: {e}")

        return packages

    def _parse_gemfile(self, content: str) -> List[Dict[str, Any]]:
        """Parse Gemfile."""
        packages = []

        for line in content.split("\n"):
            line = line.strip()

            # Match gem 'name', 'version' or gem "name", "version"
            match = re.match(
                r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?", line
            )
            if match:
                packages.append(
                    {
                        "name": match.group(1),
                        "version": match.group(2),
                        "ecosystem": "rubygems",
                    }
                )

        return packages

    def _parse_gemfile_lock(self, content: str) -> List[Dict[str, Any]]:
        """Parse Gemfile.lock."""
        packages = []
        in_specs = False

        for line in content.split("\n"):
            if line.strip() == "specs:":
                in_specs = True
                continue

            if in_specs:
                # Match "    gem_name (version)"
                match = re.match(r"^\s{4}([a-zA-Z0-9_-]+)\s+\(([^)]+)\)", line)
                if match:
                    packages.append(
                        {
                            "name": match.group(1),
                            "version": match.group(2),
                            "ecosystem": "rubygems",
                        }
                    )
                elif line and not line.startswith(" "):
                    in_specs = False

        return packages

    def _parse_composer_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse composer.json file."""
        packages = []

        try:
            data = json.loads(content)

            for dep_type in ["require", "require-dev"]:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    if name == "php" or name.startswith("ext-"):
                        continue
                    packages.append(
                        {
                            "name": name,
                            "version": self._clean_version(version),
                            "ecosystem": "packagist",
                            "dev": dep_type == "require-dev",
                        }
                    )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse composer.json: {e}")

        return packages

    def _parse_pom_xml(self, content: str) -> List[Dict[str, Any]]:
        """Parse Maven pom.xml file."""
        packages = []

        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(content)

            # Handle namespace
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}

            for dep in root.findall(".//m:dependency", ns) + root.findall(
                ".//dependency"
            ):
                group_id = dep.findtext("m:groupId", "", ns) or dep.findtext(
                    "groupId", ""
                )
                artifact_id = dep.findtext("m:artifactId", "", ns) or dep.findtext(
                    "artifactId", ""
                )
                version = dep.findtext("m:version", "", ns) or dep.findtext(
                    "version", ""
                )

                if group_id and artifact_id:
                    packages.append(
                        {
                            "name": f"{group_id}:{artifact_id}",
                            "version": version or None,
                            "ecosystem": "maven",
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to parse pom.xml: {e}")

        return packages

    def _parse_go_mod(self, content: str) -> List[Dict[str, Any]]:
        """Parse go.mod file."""
        packages = []

        for line in content.split("\n"):
            line = line.strip()

            # Match require statements
            match = re.match(r"^\s*([^\s]+)\s+v?([^\s]+)", line)
            if match and not line.startswith("module") and not line.startswith("go "):
                packages.append(
                    {
                        "name": match.group(1),
                        "version": match.group(2),
                        "ecosystem": "go",
                    }
                )

        return packages

    def _parse_cargo_toml(self, content: str) -> List[Dict[str, Any]]:
        """Parse Cargo.toml file."""
        packages = []

        try:
            import tomllib

            data = tomllib.loads(content)

            for section in ["dependencies", "dev-dependencies", "build-dependencies"]:
                deps = data.get(section, {})
                for name, spec in deps.items():
                    version = None
                    if isinstance(spec, str):
                        version = spec
                    elif isinstance(spec, dict):
                        version = spec.get("version")

                    packages.append(
                        {
                            "name": name,
                            "version": version,
                            "ecosystem": "cargo",
                            "dev": section != "dependencies",
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to parse Cargo.toml: {e}")

        return packages

    def _clean_version(self, version: str) -> Optional[str]:
        """Clean version string by removing operators."""
        if not version:
            return None

        # Remove common version operators
        version = re.sub(r"^[~^>=<!\s]+", "", version)
        version = version.strip()

        return version if version else None

    def match_packages_to_cves(
        self,
        db: Session,
        packages: List[Dict[str, Any]],
        ecosystem: str,
    ) -> List[Dict[str, Any]]:
        """
        Match packages to known CVEs using optimized batch query.

        Args:
            db: Database session
            packages: List of packages with name, version, ecosystem
            ecosystem: Package ecosystem (npm, pypi, etc.)

        Returns:
            List of matches with package and vulnerability info
        """
        if not packages:
            return []

        matches = []

        # Build package info map with CPE mappings
        package_info = {}
        all_search_patterns = set()

        for package in packages:
            package_name = package["name"].lower()
            package_version = package.get("version")

            # Get CPE mapping for this package
            vendor, product = self._get_cpe_mapping(db, ecosystem, package_name)

            # Normalize names for matching
            product_normalized = product.lower().replace("-", "_").replace(".", "_")
            package_normalized = package_name.replace("-", "_").replace(".", "_")

            # Build search patterns for this package
            patterns = {
                product_normalized,
                package_normalized,
                product.lower(),
                package_name,
            }
            if vendor:
                patterns.add(vendor.lower())

            package_info[package_name] = {
                "original_name": package["name"],
                "version": package_version,
                "vendor": vendor,
                "product": product,
                "patterns": patterns,
            }
            all_search_patterns.update(patterns)

        # Single batch query for all vulnerabilities matching any package
        # Only search in affected_products (CPE field) for better performance
        unique_patterns = set()
        for pattern in all_search_patterns:
            if len(pattern) >= 3:  # Skip very short patterns
                unique_patterns.add(pattern)

        if not unique_patterns:
            return []

        # Use PostgreSQL regex for faster matching with single condition
        # Build regex pattern: (pattern1|pattern2|pattern3|...)
        regex_pattern = "(" + "|".join(re.escape(p) for p in unique_patterns) + ")"

        # Execute single query with regex - much faster than multiple OR conditions
        vulnerabilities = (
            db.query(Vulnerability)
            .filter(
                func.lower(func.cast(Vulnerability.affected_products, sa.Text)).op("~")(
                    regex_pattern
                )
            )
            .order_by(Vulnerability.priority_score.desc())
            .limit(300)  # Reduced limit for faster response
            .all()
        )

        # Match vulnerabilities to packages
        for vuln in vulnerabilities:
            for pkg_name, pkg_info in package_info.items():
                match_type, confidence, matched_cpe = self._calculate_match(
                    vuln,
                    pkg_info["vendor"],
                    pkg_info["product"],
                    pkg_name,
                    pkg_info["version"],
                )

                if confidence > 0.3:  # Minimum confidence threshold
                    matches.append(
                        {
                            "package_name": pkg_info["original_name"],
                            "package_version": pkg_info["version"],
                            "ecosystem": ecosystem,
                            "vulnerability": vuln,
                            "match_type": match_type,
                            "match_confidence": confidence,
                            "matched_cpe": matched_cpe,
                            "matched_vendor": pkg_info["vendor"],
                            "matched_product": pkg_info["product"],
                        }
                    )

        return matches

    def _get_cpe_mapping(
        self, db: Session, ecosystem: str, package_name: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get CPE vendor/product mapping for a package."""
        # Check known mappings first (no DB query needed)
        ecosystem_mappings = KNOWN_MAPPINGS.get(ecosystem, {})
        if package_name in ecosystem_mappings:
            return ecosystem_mappings[package_name]

        # Default: use package name as product (skip DB query for performance)
        # DB lookup is expensive and rarely has custom mappings
        return None, package_name

    def _find_matching_cves(
        self,
        db: Session,
        vendor: Optional[str],
        product: str,
        package_name: str,
        package_version: Optional[str],
    ) -> List[Tuple[Vulnerability, str, float, Optional[str]]]:
        """
        Find CVEs matching a package.

        Returns list of (vulnerability, match_type, confidence, matched_cpe)
        """
        results = []

        # Normalize names for matching
        product_normalized = product.lower().replace("-", "_").replace(".", "_")
        package_normalized = package_name.lower().replace("-", "_").replace(".", "_")

        # Build search patterns
        search_patterns = [
            product_normalized,
            package_normalized,
            product.lower(),
            package_name.lower(),
        ]

        # Query vulnerabilities
        # We search in products, vendors, and affected_products (CPE) fields
        # Note: products/vendors are stored as JSON arrays, not PostgreSQL arrays
        query = db.query(Vulnerability)

        # Build OR conditions for product matching using JSON containment
        # We use text-based search on the JSON cast to text for flexibility
        conditions = []
        for pattern in set(search_patterns):
            # Check if pattern is in products JSON array (cast to text for LIKE search)
            conditions.append(
                func.lower(func.cast(Vulnerability.products, sa.Text)).contains(pattern)
            )
            # Also check affected_products (CPE strings)
            conditions.append(
                func.lower(
                    func.cast(Vulnerability.affected_products, sa.Text)
                ).contains(pattern)
            )

        if vendor:
            vendor_normalized = vendor.lower()
            conditions.append(
                func.lower(func.cast(Vulnerability.vendors, sa.Text)).contains(
                    vendor_normalized
                )
            )

        if conditions:
            query = query.filter(or_(*conditions))

        # Limit results for performance
        vulnerabilities = (
            query.order_by(Vulnerability.priority_score.desc()).limit(100).all()
        )

        for vuln in vulnerabilities:
            match_type, confidence, matched_cpe = self._calculate_match(
                vuln, vendor, product, package_name, package_version
            )

            if confidence > 0.3:  # Minimum confidence threshold
                results.append((vuln, match_type, confidence, matched_cpe))

        return results

    def _calculate_match(
        self,
        vuln: Vulnerability,
        vendor: Optional[str],
        product: str,
        package_name: str,
        package_version: Optional[str],
    ) -> Tuple[str, float, Optional[str]]:
        """
        Calculate match type and confidence for a vulnerability.

        Returns (match_type, confidence, matched_cpe)
        """
        confidence = 0.0
        match_type = "product_name"
        matched_cpe = None

        product_lower = product.lower()
        package_lower = package_name.lower()

        # Check affected_products (CPE URIs)
        if vuln.affected_products:
            for cpe in vuln.affected_products:
                cpe_lower = cpe.lower()
                parts = cpe_lower.split(":")

                if len(parts) >= 5:
                    cpe_vendor = parts[3]
                    cpe_product = parts[4]

                    # Exact product match in CPE
                    if cpe_product == product_lower or cpe_product == package_lower:
                        matched_cpe = cpe
                        confidence = 0.9

                        # Check version if available
                        if package_version and len(parts) >= 6:
                            cpe_version = parts[5]
                            if cpe_version != "*" and cpe_version != "-":
                                if package_version == cpe_version:
                                    match_type = "exact_version"
                                    confidence = 1.0
                                else:
                                    match_type = "version_range"
                                    confidence = 0.7
                        else:
                            match_type = "product_match"

                        # Vendor match bonus
                        if vendor and cpe_vendor == vendor.lower():
                            confidence = min(confidence + 0.1, 1.0)

                        break

        # Fallback: check products array
        if confidence == 0 and vuln.products:
            for prod in vuln.products:
                prod_lower = prod.lower().replace(" ", "_").replace("-", "_")
                if prod_lower == product_lower or prod_lower == package_lower:
                    match_type = "product_name"
                    confidence = 0.6
                    break

        return match_type, confidence, matched_cpe

    def create_tech_stack(
        self,
        db: Session,
        name: str,
        packages: List[Dict[str, Any]],
        source_type: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> TechStack:
        """
        Create a new tech stack and scan for vulnerabilities.

        Args:
            db: Database session
            name: Stack name
            packages: List of packages
            source_type: Source file type
            session_id: Anonymous session ID
            user_id: Authenticated user ID
            description: Optional description

        Returns:
            Created TechStack
        """
        # Create tech stack
        tech_stack = TechStack(
            name=name,
            description=description,
            session_id=session_id,
            user_id=user_id,
            packages=packages,
            source_type=source_type,
            package_count=len(packages),
        )
        db.add(tech_stack)
        db.flush()

        # Scan for vulnerabilities
        self.scan_tech_stack(db, tech_stack)

        db.commit()
        return tech_stack

    def scan_tech_stack(self, db: Session, tech_stack: TechStack) -> None:
        """
        Scan a tech stack for vulnerabilities and update matches.

        Args:
            db: Database session
            tech_stack: TechStack to scan
        """
        # Clear existing matches
        db.query(TechStackMatch).filter(
            TechStackMatch.tech_stack_id == tech_stack.id
        ).delete()

        # Get ecosystem from first package or source type
        ecosystem = "npm"  # Default
        if tech_stack.packages and len(tech_stack.packages) > 0:
            ecosystem = tech_stack.packages[0].get("ecosystem", "npm")

        # Match packages to CVEs
        matches = self.match_packages_to_cves(db, tech_stack.packages, ecosystem)

        # Create match records
        vulnerable_packages = set()
        critical_count = 0
        high_count = 0

        for match in matches:
            vuln = match["vulnerability"]

            # Create match record
            tech_match = TechStackMatch(
                tech_stack_id=tech_stack.id,
                vulnerability_id=vuln.id,
                package_name=match["package_name"],
                package_version=match["package_version"],
                ecosystem=match["ecosystem"],
                match_type=match["match_type"],
                match_confidence=match["match_confidence"],
                matched_cpe=match["matched_cpe"],
                matched_vendor=match["matched_vendor"],
                matched_product=match["matched_product"],
            )
            db.add(tech_match)

            vulnerable_packages.add(match["package_name"])

            if vuln.severity == "CRITICAL":
                critical_count += 1
            elif vuln.severity == "HIGH":
                high_count += 1

        # Update tech stack statistics
        tech_stack.vulnerable_count = len(vulnerable_packages)
        tech_stack.critical_count = critical_count
        tech_stack.high_count = high_count
        tech_stack.last_scanned_at = datetime.now(timezone.utc)

        logger.info(
            f"Scanned tech stack {tech_stack.id}: "
            f"{len(vulnerable_packages)} vulnerable packages, "
            f"{critical_count} critical, {high_count} high"
        )

    def get_tech_stack_results(self, db: Session, tech_stack_id: int) -> Dict[str, Any]:
        """
        Get scan results for a tech stack.

        Args:
            db: Database session
            tech_stack_id: TechStack ID

        Returns:
            Dict with tech stack info and matches
        """
        tech_stack = db.query(TechStack).filter(TechStack.id == tech_stack_id).first()

        if not tech_stack:
            return None

        # Get matches with vulnerability details
        matches = (
            db.query(TechStackMatch)
            .filter(TechStackMatch.tech_stack_id == tech_stack_id)
            .order_by(TechStackMatch.match_confidence.desc())
            .all()
        )

        # Group by package
        packages_with_vulns = {}
        for match in matches:
            pkg_key = match.package_name

            if pkg_key not in packages_with_vulns:
                packages_with_vulns[pkg_key] = {
                    "name": match.package_name,
                    "version": match.package_version,
                    "ecosystem": match.ecosystem,
                    "vulnerabilities": [],
                }

            packages_with_vulns[pkg_key]["vulnerabilities"].append(
                {
                    "cve_id": match.vulnerability.cve_id,
                    "severity": match.vulnerability.severity,
                    "cvss_score": match.vulnerability.cvss_score,
                    "title": match.vulnerability.title,
                    "description": (
                        match.vulnerability.description[:200]
                        if match.vulnerability.description
                        else None
                    ),
                    "match_type": match.match_type,
                    "match_confidence": match.match_confidence,
                    "exploited": match.vulnerability.exploited_in_the_wild,
                }
            )

        return {
            "id": tech_stack.id,
            "name": tech_stack.name,
            "description": tech_stack.description,
            "source_type": tech_stack.source_type,
            "package_count": tech_stack.package_count,
            "vulnerable_count": tech_stack.vulnerable_count,
            "critical_count": tech_stack.critical_count,
            "high_count": tech_stack.high_count,
            "last_scanned_at": tech_stack.last_scanned_at,
            "created_at": tech_stack.created_at,
            "packages": list(packages_with_vulns.values()),
            "all_packages": tech_stack.packages,
        }


# Singleton instance
_techstack_service = None


def get_techstack_service() -> TechStackService:
    """Get singleton TechStackService instance."""
    global _techstack_service
    if _techstack_service is None:
        _techstack_service = TechStackService()
    return _techstack_service
