#!/usr/bin/env python3
"""
License Validation Script
Validates that all dependencies use approved licenses.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Set


class LicenseValidator:
    """Validates dependency licenses against approved list."""
    
    # Approved open source licenses
    APPROVED_LICENSES = {
        'MIT License',
        'MIT',
        'Apache Software License',
        'Apache 2.0',
        'Apache-2.0',
        'BSD License',
        'BSD-3-Clause',
        'BSD-2-Clause',
        'ISC License',
        'ISC',
        'Python Software Foundation License',
        'PSF',
        'Mozilla Public License 2.0 (MPL 2.0)',
        'MPL-2.0',
        'GNU Lesser General Public License v3 (LGPLv3)',
        'LGPL-3.0',
        'GNU Lesser General Public License v2 (LGPLv2)',
        'LGPL-2.1',
        'The Unlicense',
        'Unlicense',
        'CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'CC0-1.0'
    }
    
    # Licenses that require review
    REVIEW_REQUIRED = {
        'GNU General Public License v3 (GPLv3)',
        'GPL-3.0',
        'GNU General Public License v2 (GPLv2)', 
        'GPL-2.0',
        'GNU Affero General Public License v3 (AGPLv3)',
        'AGPL-3.0',
        'European Union Public License 1.2 (EUPL 1.2)',
        'EUPL-1.2'
    }
    
    # Licenses that are not allowed
    FORBIDDEN_LICENSES = {
        'Commercial',
        'Proprietary',
        'Unknown',
        'UNKNOWN',
        'Copyleft',
        'Viral'
    }

    def __init__(self):
        self.issues = []
        self.warnings = []

    def validate_licenses(self, license_file: Path) -> bool:
        """Validate all licenses in the license report."""
        try:
            with open(license_file, 'r') as f:
                licenses = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error reading license file: {e}")
            return False
        
        print(f"📄 Validating licenses for {len(licenses)} dependencies...")
        
        approved_count = 0
        review_count = 0
        forbidden_count = 0
        
        for package in licenses:
            package_name = package.get('Name', 'Unknown')
            license_name = package.get('License', 'Unknown')
            version = package.get('Version', 'Unknown')
            
            # Normalize license name
            license_normalized = self._normalize_license_name(license_name)
            
            if license_normalized in self.APPROVED_LICENSES:
                approved_count += 1
                print(f"✅ {package_name} ({version}): {license_name}")
                
            elif license_normalized in self.REVIEW_REQUIRED:
                review_count += 1
                self.warnings.append({
                    "type": "LICENSE_REQUIRES_REVIEW",
                    "package": package_name,
                    "version": version,
                    "license": license_name,
                    "message": f"License requires legal review: {license_name}"
                })
                print(f"⚠️  {package_name} ({version}): {license_name} - REVIEW REQUIRED")
                
            elif license_normalized in self.FORBIDDEN_LICENSES or 'unknown' in license_normalized.lower():
                forbidden_count += 1
                self.issues.append({
                    "type": "FORBIDDEN_LICENSE",
                    "package": package_name,
                    "version": version,
                    "license": license_name,
                    "severity": "HIGH",
                    "message": f"Forbidden or unknown license: {license_name}"
                })
                print(f"❌ {package_name} ({version}): {license_name} - FORBIDDEN")
                
            else:
                # Unknown license - requires review
                review_count += 1
                self.warnings.append({
                    "type": "UNKNOWN_LICENSE",
                    "package": package_name,
                    "version": version,
                    "license": license_name,
                    "message": f"Unknown license requires review: {license_name}"
                })
                print(f"⚠️  {package_name} ({version}): {license_name} - UNKNOWN")
        
        # Summary
        print(f"\n📊 LICENSE SUMMARY:")
        print(f"  ✅ Approved: {approved_count}")
        print(f"  ⚠️  Requires review: {review_count}")
        print(f"  ❌ Forbidden: {forbidden_count}")
        print(f"  📦 Total packages: {len(licenses)}")
        
        # Check compliance
        if forbidden_count > 0:
            print(f"\n❌ {forbidden_count} packages with forbidden licenses detected!")
            print("🔒 Please remove or replace packages with forbidden licenses.")
            return False
            
        if review_count > 0:
            print(f"\n⚠️  {review_count} packages require legal review")
            print("📋 Please review these licenses with legal team.")
            
        return True

    def _normalize_license_name(self, license_name: str) -> str:
        """Normalize license name for comparison."""
        if not license_name:
            return "Unknown"
            
        # Common normalizations
        normalizations = {
            'Apache License 2.0': 'Apache-2.0',
            'Apache License, Version 2.0': 'Apache-2.0',
            'Apache Software License': 'Apache-2.0',
            'MIT License': 'MIT',
            'BSD License (3 clause)': 'BSD-3-Clause',
            'BSD License (2 clause)': 'BSD-2-Clause',
            'Mozilla Public License 2.0': 'MPL-2.0',
        }
        
        return normalizations.get(license_name, license_name)

    def generate_license_report(self) -> str:
        """Generate a human-readable license report."""
        report = "# License Compliance Report\n\n"
        
        if self.issues:
            report += "## ❌ Issues Found\n\n"
            for issue in self.issues:
                report += f"- **{issue['package']}** ({issue['version']}): {issue['message']}\n"
            report += "\n"
        
        if self.warnings:
            report += "## ⚠️ Warnings\n\n"
            for warning in self.warnings:
                report += f"- **{warning['package']}** ({warning['version']}): {warning['message']}\n"
            report += "\n"
        
        if not self.issues and not self.warnings:
            report += "## ✅ All Clear\n\nAll dependencies use approved licenses.\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Validate dependency licenses")
    parser.add_argument('license_file', help='JSON file with license information')
    parser.add_argument('--output-report', help='Output file for license report')
    args = parser.parse_args()
    
    license_file = Path(args.license_file)
    
    if not license_file.exists():
        print(f"❌ License file not found: {license_file}")
        return 1
    
    validator = LicenseValidator()
    success = validator.validate_licenses(license_file)
    
    # Generate report if requested
    if args.output_report:
        report = validator.generate_license_report()
        with open(args.output_report, 'w') as f:
            f.write(report)
        print(f"📋 License report written to: {args.output_report}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())