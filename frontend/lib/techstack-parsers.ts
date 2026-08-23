/**
 * Client-side dependency file parsers, shared by the one-shot /scan page
 * and the persistent /my-stack tracker. Parsing happens in the browser
 * (rather than uploading the raw file) to avoid Cloudflare/WAF blocking
 * on file uploads.
 */

export interface ParsedPackage {
  name: string;
  version: string | null;
  ecosystem: string;
  dev: boolean;
}

/**
 * Parse a dependency file's contents into a package list.
 * Throws an Error with a user-facing message on unsupported/invalid input.
 */
export function parseDependencyFile(fileName: string, fileContent: string): ParsedPackage[] {
  const packages: ParsedPackage[] = [];
  const name = fileName.toLowerCase();

  const isPackageJson = name === "package.json" || name.endsWith("package.json");
  const isPackageLock = name === "package-lock.json" || name.endsWith("package-lock.json");
  const isRequirementsTxt = name === "requirements.txt" || name.endsWith(".txt") || name.includes("requirements");
  const isGemfile = name === "gemfile" || name === "gemfile.lock" || name.startsWith("gemfile");
  const isComposerJson = name === "composer.json" || name.endsWith("composer.json");
  const isGoMod = name === "go.mod" || name.endsWith(".mod");
  const isCargoToml = name === "cargo.toml" || name.endsWith("cargo.toml");
  const isPomXml = name === "pom.xml" || name.endsWith(".xml");

  if (isPackageJson || isPackageLock) {
    try {
      const json = JSON.parse(fileContent);

      if (json.dependencies) {
        for (const [pkgName, version] of Object.entries(json.dependencies)) {
          packages.push({
            name: pkgName,
            version: typeof version === "string" ? version.replace(/^[\^~>=<]/, "") : null,
            ecosystem: "npm",
            dev: false,
          });
        }
      }

      if (json.devDependencies) {
        for (const [pkgName, version] of Object.entries(json.devDependencies)) {
          packages.push({
            name: pkgName,
            version: typeof version === "string" ? version.replace(/^[\^~>=<]/, "") : null,
            ecosystem: "npm",
            dev: true,
          });
        }
      }
    } catch {
      throw new Error("Invalid package.json format");
    }
  } else if (isRequirementsTxt) {
    const lines = fileContent.split("\n");

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#") || trimmed.startsWith("-")) continue;

      const match = trimmed.match(/^([a-zA-Z0-9_-]+)(?:\[.*?\])?(?:([=<>!~]+)(.+))?$/);
      if (match) {
        packages.push({
          name: match[1],
          version: match[3] || null,
          ecosystem: "pypi",
          dev: false,
        });
      }
    }
  } else if (isGemfile) {
    const gemRegex = /gem\s+['"]([^'"]+)['"](?:,\s*['"]([^'"]+)['"])?/g;
    let match;
    while ((match = gemRegex.exec(fileContent)) !== null) {
      packages.push({
        name: match[1],
        version: match[2] || null,
        ecosystem: "rubygems",
        dev: false,
      });
    }
  } else if (isComposerJson) {
    try {
      const json = JSON.parse(fileContent);
      const allDeps = { ...json.require, ...json["require-dev"] };
      for (const [pkgName, version] of Object.entries(allDeps)) {
        if (pkgName === "php") continue;
        packages.push({
          name: pkgName,
          version: typeof version === "string" ? version : null,
          ecosystem: "packagist",
          dev: false,
        });
      }
    } catch {
      throw new Error("Invalid composer.json format");
    }
  } else if (isGoMod) {
    const requireRegex = /require\s+([^\s]+)\s+v?([^\s]+)/g;
    let match;
    while ((match = requireRegex.exec(fileContent)) !== null) {
      packages.push({
        name: match[1],
        version: match[2],
        ecosystem: "go",
        dev: false,
      });
    }
  } else if (isCargoToml) {
    const depRegex = /^([a-zA-Z0-9_-]+)\s*=\s*["']([^"']+)["']/gm;
    let match;
    while ((match = depRegex.exec(fileContent)) !== null) {
      packages.push({
        name: match[1],
        version: match[2],
        ecosystem: "cargo",
        dev: false,
      });
    }
  } else if (isPomXml) {
    const depRegex = /<artifactId>([^<]+)<\/artifactId>[\s\S]*?<version>([^<]+)<\/version>/g;
    let match;
    while ((match = depRegex.exec(fileContent)) !== null) {
      packages.push({
        name: match[1],
        version: match[2],
        ecosystem: "maven",
        dev: false,
      });
    }
  } else {
    throw new Error(`Unsupported file format: ${fileName}`);
  }

  if (packages.length === 0) {
    throw new Error("No packages found in the file. Please check the file format.");
  }

  return packages;
}
