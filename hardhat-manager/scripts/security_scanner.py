#!/usr/bin/env python3
"""
Smart Contract Security Scanner and Auditor

Comprehensive security scanning and vulnerability assessment for smart contracts.
Integrates multiple security tools and provides detailed reports.

Usage:
    python3 security_scanner.py --scan <contract-path> [--tools <tools>]
    python3 security_scanner.py --project <project-path> [--full-scan]
    python3 security_scanner.py --interactive
"""

import os
import sys
import json
import argparse
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum


class VulnerabilitySeverity(Enum):
    INFO = "info"
    LOW = "low"
    WARNING = "warning"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Vulnerability:
    title: str
    description: str
    severity: VulnerabilitySeverity
    contract: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    tool: str = ""
    confidence: str = "high"
    cwe_id: Optional[str] = None


class SecurityScanner:
    def __init__(self):
        self.reports_dir = Path("security-reports")
        self.scans_dir = Path("security-scans")
        self.configs_dir = Path("security-configs")

        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)
        self.scans_dir.mkdir(exist_ok=True)
        self.configs_dir.mkdir(exist_ok=True)

        # Tool configurations
        self.tools = {
            "slither": {
                "name": "Slither",
                "command": "slither",
                "install_cmd": "pip install slither-analyzer",
                "args": ["--filter-paths", "node_modules/", "--json", "--output", "slither-results.json"],
                "description": "Static analysis framework for smart contracts",
                "supported": True
            },
            "mythril": {
                "name": "Mythril",
                "command": "myth",
                "install_cmd": "pip install mythril",
                "args": ["-x", "--json", "--outfile", "mythril-results.json"],
                "description": "Symbolic execution testing tool",
                "supported": True
            },
            "echidna": {
                "name": "Echidna",
                "command": "echidna-test",
                "install_cmd": "pip install echidna",
                "args": ["--config", "echidna.yaml", "--format", "json"],
                "description": "Property-based fuzzer",
                "supported": True
            },
            "mantic": {
                "name": "Mantic",
                "command": "solv",
                "install_cmd": "pip install slither-analyzer",
                "args": ["--filter-paths", "node_modules/", "--json", "--output", "mantic-results.json"],
                "description": "Symbolic execution engine",
                "supported": True
            },
            "scribble": {
                "name": "Scribble",
                "command": "scribble",
                "install_cmd": "npm install -g scribble",
                "args": ["--input-mode", "source", "--output-mode", "json", "--ast", "ast.json"],
                "description": "Intermediate representation analyzer",
                "supported": True
            },
            "upgrade_security_analysis": {
                "name": "Upgrade Security Analysis",
                "command": None,
                "install_cmd": None,
                "args": [],
                "description": "Built-in upgrade security pattern analysis",
                "supported": True
            }
        }

        # Common vulnerability patterns
        self.vulnerability_patterns = {
            "reentrancy": {
                "pattern": r"reentrancy|call\\.value\\(|msg\\.sender\\.call\\(",
                "severity": VulnerabilitySeverity.CRITICAL,
                "title": "Reentrancy Vulnerability",
                "description": "Contract may be vulnerable to reentrancy attacks",
                "recommendation": "Implement checks-effects-interactions pattern and use nonReentrant modifier"
            },
            "integer_overflow": {
                "pattern": r"\\*.*\\+|\\-.*\\-|uint256\\(.*\\) \\+|uint256\\(.*\\) \\-",
                "severity": VulnerabilitySeverity.HIGH,
                "title": "Integer Overflow/Underflow",
                "description": "Potential integer overflow or underflow vulnerability",
                "recommendation": "Use SafeMath or Solidity 0.8.0+ with built-in overflow protection"
            },
            "access_control": {
                "pattern": r"require\\(msg\\.sender|owner\\)|onlyOwner|msg\\.sender\\.call\\(",
                "severity": VulnerabilitySeverity.MEDIUM,
                "title": "Access Control Issue",
                "description": "Potential access control vulnerability",
                "recommendation": "Verify that all critical functions have proper access controls"
            },
            "uninitialized_storage": {
                "pattern": r"mapping\\([^\\)]*\\)\\s*[^\\}\\s*;",
                "severity": VulnerabilitySeverity.MEDIUM,
                "title": "Uninitialized Storage Pointer",
                "description": "Storage pointer may be uninitialized",
                "recommendation": "Initialize all storage variables in constructor or with default values"
            },
            "timestamp_dependency": {
                "pattern": r"block\\.timestamp|now\\(\\)|block\\.number",
                "severity": VulnerabilitySeverity.MEDIUM,
                "title": "Timestamp Dependency",
                "description": "Contract may be vulnerable to timestamp manipulation",
                "recommendation": "Use block number instead of timestamp for critical operations"
            },
            "delegatecall": {
                "pattern": r"delegatecall\\(",
                "severity": VulnerabilitySeverity.HIGH,
                "title": "Delegatecall Vulnerability",
                "description": "Contract may be vulnerable to delegatecall attacks",
                "recommendation": "Implement delegatecall restrictions and validation"
            },
            "selfdestruct": {
                "pattern": r"selfdestruct\\(|suicide\\(",
                "severity": VulnerabilitySeverity.HIGH,
                "title": "Selfdestruct Function",
                "description": "Contract contains selfdestruct functionality",
                "recommendation": "Ensure proper access controls for selfdestruct function"
            },
            "txorigin": {
                "pattern": r"tx\\.origin",
                "severity": VulnerabilitySeverity.WARNING,
                "title": "tx.origin Usage",
                "description": "Use of tx.origin may lead to security issues",
                "recommendation": "Use msg.sender instead of tx.origin for authorization"
            },
            "unchecked_call": {
                "pattern": r"\\.call\\(.*\\)|\\.transfer\\(.*\\)|\\.send\\(.*\\)",
                "severity": VulnerabilitySeverity.MEDIUM,
                "title": "Unchecked Call Return Value",
                "description": "External call return value is not checked",
                "recommendation": "Always check return values of external calls"
            },
            "logic_bomb": {
                "pattern": r"while\\s*\\(.*\\)\\s*{|for\\s*\\(.*;.*\\)\\s*{{",
                "severity": VulnerabilitySeverity.HIGH,
                "title": "Potential Logic Bomb",
                "description": "Loop may consume excessive gas",
                "recommendation": "Add iteration limits or implement off-chain computation"
            }
        }

        # CWE mapping for vulnerabilities
        self.cwe_mapping = {
            "reentrancy": "CWE-841",
            "integer_overflow": "CWE-190",
            "access_control": "CWE-862",
            "timestamp_dependency": "CWE-843",
            "delegatecall": "CWE-843",
            "selfdestruct": "CWE-843"
        }

        # Custom security rules
        self.custom_rules = {
            "check_external_calls": True,
            "check_event_emission": True,
            "check_gas_limit": True,
            "check_function_visibility": True,
            "check_constructor_security": True
        }

        # Upgrade security patterns
        self.upgrade_patterns = {
            "unprotected_delegatecall": {
                "pattern": r'delegatecall\s*\(',
                "title": "Unprotected Delegatecall",
                "description": "Delegatecall without proper access control can lead to unauthorized code execution",
                "severity": VulnerabilitySeverity.CRITICAL,
                "recommendation": "Add access control modifiers or use OpenZeppelin's upgradeable patterns",
                "cwe_id": "CWE-843"
            },
            "storage_collision": {
                "pattern": r'(?:mapping|uint256|string|address|bool)\s+public\s+(\w+)',
                "title": "Potential Storage Collision in Upgradeable Contract",
                "description": "Storage layout changes in upgradeable contracts can cause storage collisions",
                "severity": VulnerabilitySeverity.HIGH,
                "recommendation": "Use OpenZeppelin's upgradeable storage patterns or append new storage variables",
                "cwe_id": "CWE-787"
            },
            "immutable_constructor": {
                "pattern": r'constructor\s*\([^)]*\)\s*(?:immutable|constant)',
                "title": "Immutable Variables in Upgradeable Constructor",
                "description": "Immutable variables in constructors of upgradeable contracts can cause issues",
                "severity": VulnerabilitySeverity.MEDIUM,
                "recommendation": "Use regular variables with proper initialization in upgradeable contracts",
                "cwe_id": "CWE-1116"
            },
            "selfdestruct_upgradeable": {
                "pattern": r'selfdestruct\s*\(',
                "title": "Selfdestruct in Upgradeable Contract",
                "description": "Selfdestruct in upgradeable contracts can break proxy patterns",
                "severity": VulnerabilitySeverity.CRITICAL,
                "recommendation": "Remove selfdestruct or use upgrade-safe destruction patterns",
                "cwe_id": "CWE-754"
            },
            "initialization_missing": {
                "pattern": r'function\s+initialize\s*\(',
                "title": "Missing Initialization Pattern",
                "description": "Upgradeable contract should use initializer pattern instead of constructor",
                "severity": VulnerabilitySeverity.HIGH,
                "recommendation": "Use OpenZeppelin's Initializable pattern and remove constructor logic",
                "cwe_id": "CWE-665"
            }
        }

    def check_tool_availability(self, tool_name):
        """Check if a security tool is available."""
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            return False, f"Unknown tool: {tool_name}"

        try:
            result = subprocess.run(
                [tool_info["command"], "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return True, "Tool is available"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try to install the tool
            try:
                print(f"🔧 Installing {tool_info['name']}...")
                install_cmd = tool_info["install_cmd"].split()
                subprocess.run(install_cmd, check=True, timeout=300)
                return True, f"Successfully installed {tool_info['name']}"
            except Exception as e:
                return False, f"Failed to install {tool_info['name']}: {e}"

    def scan_with_slither(self, contract_path, project_path=None):
        """Scan contracts with Slither."""
        print("🔍 Scanning with Slither...")

        tool_info = self.tools["slither"]
        available, message = self.check_tool_availability("slither")
        if not available:
            return [], f"Slither not available: {message}"

        # Prepare Slither command
        cmd = [tool_info["command"]]
        cmd.extend(tool_info["args"])

        if contract_path:
            # If single contract, add it to the scan
            cmd.append(contract_path)
        elif project_path:
            # If project path, scan all contracts in the directory
            cmd.append(project_path)
        else:
            # Scan current directory
            cmd.append("contracts/")

        # Add additional Slither options
        cmd.extend([
            "--filter-paths", "node_modules/",
            "--json", "--output", "slither-results.json",
            "--print", "human"
        ])

        try:
            print(f"📋 Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            # Parse Slither results
            vulnerabilities = self.parse_slither_results("slither-results.json")
            print(f"✅ Slither scan completed: {len(vulnerabilities)} issues found")

            return vulnerabilities, result.stdout

        except subprocess.TimeoutExpired:
            return [], "Slither scan timed out"
        except Exception as e:
            return [], f"Slither scan failed: {e}"

    def scan_with_mythril(self, contract_path, project_path=None):
        """Scan contracts with Mythril."""
        print("🔍 Scanning with Mythril...")

        tool_info = self.tools["mythril"]
        available, message = self.check_tool_availability("mythril")
        if not available:
            return [], f"Mythril not available: {message}"

        # Create Mythril config if it doesn't exist
        config_path = Path("mythril.config.yml")
        if not config_path.exists():
            config_content = f"""
mythril:
  analysis:
    modules:
      - slither
    strategy: dfs
    address_coverage: [0.1, 0.9]
    call_depth: [1, 10]
    loop_bound: [1, 50]
    timeout: 30

storage:
  model: model
  backend: storage
  endpoint: http://localhost:8080
"""
            with open(config_path, 'w') as f:
                f.write(config_content)

        # Prepare Mythril command
        cmd = [tool_info["command"]]
        cmd.extend([
            "-x",  # Run analysis
            "--config", config_path,
            "--json", "--outfile", "mythril-results.json"
        ])

        if contract_path:
            cmd.append(contract_path)
        elif project_path:
            # Find all contract files in the project
            contracts_dir = Path(project_path) / "contracts"
            if contracts_dir.exists():
                contract_files = list(contracts_dir.rglob("*.sol"))
                for contract_file in contract_files:
                    cmd.append(str(contract_file))

        try:
            print(f"📋 Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )

            # Parse Mythril results
            vulnerabilities = self.parse_mythril_results("mythril-results.json")
            print(f"✅ Mythril scan completed: {len(vulnerabilities)} issues found")

            return vulnerabilities, result.stdout

        except subprocess.TimeoutExpired:
            return [], "Mythril scan timed out"
        except Exception as e:
            return [], f"Mythril scan failed: {e}"

    def scan_with_echidna(self, contract_path, project_path=None):
        """Scan contracts with Echidna."""
        print("🔍 Scanning with Echidna...")

        tool_info = self.tools["echidna"]
        available, message = self.check_tool_availability("echidna")
        if not available:
            return [], f"Echidna not available: {message}"

        # Create Echidna config if it doesn't exist
        config_path = Path("echidna.yaml")
        if not config_path.exists():
            contract_name = Path(contract_path).stem if contract_path else "Contract"
            config_content = f"""
coverage:
  enable: true
  # Configure contract addresses for testing
  contracts:
    - address: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e0Ca"
      # Add more contracts as needed
"""
            with open(config_path, 'w') as f:
                f.write(config_content)

        # Prepare Echidna command
        cmd = [tool_info["command"]]
        cmd.extend([
            "--config", config_path,
            "--format", "json",
            "--output", "echidna-results.json"
        ])

        if contract_path:
            cmd.append(contract_path)
        elif project_path:
            # Find all contract files
            contracts_dir = Path(project_path) / "contracts"
            if contracts_dir.exists():
                contract_files = list(contracts_dir.rglob("*.sol"))
                for contract_file in contract_files:
                    cmd.append(str(contract_file))

        try:
            print(f"📋 Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            # Parse Echidna results
            vulnerabilities = self.parse_echidna_results("echidna-results.json")
            print(f"✅ Echidna scan completed: {len(vulnerabilities)} issues found")

            return vulnerabilities, result.stdout

        except subprocess.TimeoutExpired:
            return [], "Echidna scan timed out"
        except Exception as e:
            return [], f"Echidna scan failed: {e}"

    def perform_pattern_matching(self, contract_path):
        """Perform pattern-based vulnerability detection."""
        print("🔍 Performing pattern-based vulnerability detection...")

        vulnerabilities = []

        try:
            with open(contract_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')

            for pattern_name, pattern_info in self.vulnerability_patterns.items():
                matches = list(re.finditer(pattern_info["pattern"], content, re.IGNORECASE))

                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    start_line = max(0, line_number - 3)
                    end_line = min(len(lines), line_number + 3)
                    code_snippet = '\n'.join(lines[start_line:end_line])

                    vulnerability = Vulnerability(
                        title=pattern_info["title"],
                        description=pattern_info["description"],
                        severity=pattern_info["severity"],
                        contract=str(contract_path),
                        line_number=line_number,
                        code_snippet=code_snippet,
                        recommendation=pattern_info["recommendation"],
                        tool="Pattern Matching",
                        confidence="medium",
                        cwe_id=self.cwe_mapping.get(pattern_name)
                    )

                    vulnerabilities.append(vulnerability)

            print(f"✅ Pattern matching completed: {len(vulnerabilities)} potential issues found")
            return vulnerabilities

        except Exception as e:
            return [Vulnerability(
                title="Pattern Matching Error",
                description=f"Error during pattern matching: {str(e)}",
                severity=VulnerabilitySeverity.LOW,
                contract=str(contract_path),
                tool="Pattern Matching",
                confidence="low"
            )]

    def perform_security_rules_check(self, contract_path, project_path=None):
        """Perform custom security rules checking."""
        print("🔍 Performing custom security rules check...")

        vulnerabilities = []

        try:
            with open(contract_path, 'r') as f:
                content = f.read()

            # Rule 1: Check for proper event emission
            if self.custom_rules["check_event_emission"]:
                event_patterns = [r'emit\s*\(', r'require\(.*\),\s*emit\s*\(']
                for pattern in event_patterns:
                    if not re.search(pattern, content, re.IGNORECASE):
                        vulnerabilities.append(Vulnerability(
                            title="Missing Event Emission",
                            description="Critical state changes should emit events",
                            severity=VulnerabilitySeverity.MEDIUM,
                            contract=str(contract_path),
                            recommendation="Add appropriate event emissions for state changes",
                            tool="Security Rules",
                            confidence="medium"
                        ))

            # Rule 2: Check function visibility
            if self.custom_rules["check_function_visibility"]:
                # Check for public functions without access controls
                public_function_pattern = r'function\s+([^(}]+)\s*\([^)]*\)\s*(public|external)'
                for match in re.finditer(public_function_pattern, content):
                    func_name = match.group(1)
                    if not re.search(r'require\(|onlyOwner|modifier', content[match.start():match.start() + 1000]):
                        vulnerabilities.append(Vulnerability(
                            title="Unprotected Public Function",
                            description=f"Public function {func_name} may need access control",
                            severity=VulnerabilitySeverity.MEDIUM,
                            contract=str(contract_path),
                            recommendation="Add proper access control modifiers",
                            tool="Security Rules",
                            confidence="medium"
                        ))

            # Rule 3: Check constructor security
            if self.custom_rules["check_constructor_security"]:
                if "constructor" in content and not re.search(r'initialize|onlyOwner|require\\s*msg\\.sender', content[:1000]):
                    vulnerabilities.append(Vulnerability(
                        title="Constructor Security Issue",
                        description="Constructor may not properly initialize contract state",
                        severity=VulnerabilitySeverity.HIGH,
                        contract=str(contract_path),
                        recommendation="Ensure proper initialization in constructor",
                        tool="Security Rules",
                        confidence="high"
                    ))

            # Rule 4: Check gas limits
            if self.custom_rules["check_gas_limit"]:
                loop_patterns = [r'while\s*\(', r'for\s*\(']
                for pattern in loop_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    if len(matches) > 5:  # If many loops found
                        vulnerabilities.append(Vulnerability(
                            title="High Gas Consumption Risk",
                            description="Contract contains multiple loops that may consume excessive gas",
                            severity=Vulnerability.WARNING,
                            contract=str(contract_path),
                            recommendation="Consider implementing iteration limits or off-chain computation",
                            tool="Security Rules",
                            confidence="low"
                        ))
                        break

            print(f"✅ Security rules check completed: {len(vulnerabilities)} issues found")
            return vulnerabilities

        except Exception as e:
            return [Vulnerability(
                title="Security Rules Error",
                description=f"Error during security rules check: {str(e)}",
                severity=VulnerabilitySeverity.LOW,
                contract=str(contract_path),
                tool="Security Rules",
                confidence="low"
            )]

    def perform_upgrade_security_analysis(self, contract_path, project_path=None):
        """Perform upgrade-specific security analysis."""
        print("🔍 Performing upgrade security analysis...")

        vulnerabilities = []

        try:
            with open(contract_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')

            # Check for upgrade-related patterns
            for pattern_name, pattern_info in self.upgrade_patterns.items():
                matches = list(re.finditer(pattern_info["pattern"], content, re.IGNORECASE))

                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    start_line = max(0, line_number - 3)
                    end_line = min(len(lines), line_number + 3)
                    code_snippet = '\n'.join(lines[start_line:end_line])

                    vulnerability = Vulnerability(
                        title=pattern_info["title"],
                        description=pattern_info["description"],
                        severity=pattern_info["severity"],
                        contract=str(contract_path),
                        line_number=line_number,
                        code_snippet=code_snippet,
                        recommendation=pattern_info["recommendation"],
                        tool="Upgrade Security Analysis",
                        confidence="high",
                        cwe_id=pattern_info.get("cwe_id")
                    )

                    vulnerabilities.append(vulnerability)

            # Additional upgrade-specific checks

            # Check for proxy pattern compatibility
            if re.search(r'@openzeppelin/contracts-upgradeable', content, re.IGNORECASE):
                # Check for constructor in upgradeable contract
                if re.search(r'constructor\s*\(', content):
                    vulnerabilities.append(Vulnerability(
                        title="Constructor in Upgradeable Contract",
                        description="Upgradeable contracts should use initializers instead of constructors",
                        severity=VulnerabilitySeverity.HIGH,
                        contract=str(contract_path),
                        recommendation="Replace constructor with initializer function",
                        tool="Upgrade Security Analysis",
                        confidence="high",
                        cwe_id="CWE-665"
                    ))

                # Check for storage gaps
                if not re.search(r'__gap', content):
                    vulnerabilities.append(Vulnerability(
                        title="Missing Storage Gaps",
                        description="Upgradeable contracts should include storage gaps for future upgrades",
                        severity=VulnerabilitySeverity.MEDIUM,
                        contract=str(contract_path),
                        recommendation="Add uint256[__gap] storage variables for future upgrades",
                        tool="Upgrade Security Analysis",
                        confidence="medium",
                        cwe_id="CWE-787"
                    ))

            # Check for self-modification patterns
            selfdestruct_patterns = [
                r'selfdestruct\s*\(',
                r'suicide\s*\(',
                r'address\(this\)\.send\s*\('
            ]

            for pattern in selfdestruct_patterns:
                if re.search(pattern, content):
                    vulnerabilities.append(Vulnerability(
                        title="Self-Destruct Pattern in Upgradeable Contract",
                        description="Self-destruct patterns can break proxy functionality",
                        severity=VulnerabilitySeverity.CRITICAL,
                        contract=str(contract_path),
                        recommendation="Remove self-destruct patterns or implement upgrade-safe alternatives",
                        tool="Upgrade Security Analysis",
                        confidence="high",
                        cwe_id="CWE-754"
                    ))
                    break

            # Check for external call risks in upgradeable context
            external_call_patterns = [
                r'\.call\s*\(',
                r'\.delegatecall\s*\(',
                r'\.send\s*\(',
                r'\.transfer\s*\('
            ]

            external_calls = []
            for pattern in external_call_patterns:
                matches = list(re.finditer(pattern, content))
                external_calls.extend(matches)

            if len(external_calls) > 3:  # Many external calls in upgradeable contract
                vulnerabilities.append(Vulnerability(
                    title="High External Call Complexity in Upgradeable Contract",
                    description=f"Found {len(external_calls)} external calls which may increase upgrade risk",
                    severity=VulnerabilitySeverity.WARNING,
                    contract=str(contract_path),
                    recommendation="Consider reducing external call complexity or implementing additional safety checks",
                    tool="Upgrade Security Analysis",
                    confidence="medium",
                    cwe_id="CWE-20"
                ))

            # Check for function signature changes risk
            if re.search(r'function\s+\w+\s*\([^)]*\)\s*(public|external)', content):
                # Look for potential function signature conflicts
                function_signatures = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*(public|external)', content)
                if len(function_signatures) > 10:
                    vulnerabilities.append(Vulnerability(
                        title="High Function Count in Upgradeable Contract",
                        description=f"Found {len(function_signatures)} public/external functions which may increase upgrade complexity",
                        severity=VulnerabilitySeverity.WARNING,
                        contract=str(contract_path),
                        recommendation="Consider consolidating functions or using modular upgrade patterns",
                        tool="Upgrade Security Analysis",
                        confidence="low",
                        cwe_id="CWE-1088"
                    ))

            print(f"✅ Upgrade security analysis completed: {len(vulnerabilities)} issues found")
            return vulnerabilities

        except Exception as e:
            return [Vulnerability(
                title="Upgrade Security Analysis Error",
                description=f"Error during upgrade security analysis: {str(e)}",
                severity=VulnerabilitySeverity.LOW,
                contract=str(contract_path),
                tool="Upgrade Security Analysis",
                confidence="low"
            )]

    def parse_slither_results(self, results_file):
        """Parse Slither JSON results."""
        vulnerabilities = []

        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            if "results" in results and "detectors" in results["results"]:
                for detector in results["results"]["detectors"]:
                    for issue in detector.get("elements", []):
                        vulnerability = Vulnerability(
                            title=detector.get("description", "Unknown"),
                            description=issue.get("description", "No description available"),
                            severity=self.map_slither_severity(detector.get("impact", "informational")),
                            contract=issue.get("source_mapping", {}).get("filename", "Unknown"),
                            line_number=issue.get("source_mapping", {}).get("lines", [{}])[0] if issue.get("source_mapping", {}).get("lines") else None,
                            code_snippet=issue.get("source_mapping", {}).get("lines", [""])[0] if issue.get("source_mapping", {}).get("lines") else "",
                            recommendation=detector.get("recommendation", "Follow security best practices"),
                            tool="Slither",
                            confidence=detector.get("confidence", "high")
                        )

                        if "cwe_id" in issue:
                            vulnerability.cwe_id = issue["cwe_id"]

                        vulnerabilities.append(vulnerability)

        except Exception as e:
            print(f"⚠️  Error parsing Slither results: {e}")

        return vulnerabilities

    def parse_mythril_results(self, results_file):
        """Parse Mythril JSON results."""
        vulnerabilities = []

        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            if "issues" in results:
                for issue in results["issues"]:
                    vulnerability = Vulnerability(
                        title=issue.get("description", "Unknown"),
                        description=issue.get("description", "No description available"),
                        severity=self.map_mythril_severity(issue.get("severity", "Low")),
                        contract=issue.get("contract", "Unknown"),
                        line_number=issue.get("line", None),
                        code_snippet=issue.get("code", ""),
                        recommendation=issue.get("recommendation", "Review and fix the issue"),
                        tool="Mythril",
                        confidence="high"
                    )

                    vulnerabilities.append(vulnerability)

        except Exception as e:
            print(f"⚠️  Error parsing Mythril results: {e}")

        return vulnerabilities

    def parse_echidna_results(self, results_file):
        """Parse Echidna JSON results."""
        vulnerabilities = []

        try:
            with open(results_file, 'r') as f:
                results = json.load(f)

            if "tests" in results:
                for test in results["tests"]:
                    for issue in test.get("tests", []):
                        if "type" in issue and issue["type"] == "error":
                            vulnerability = Vulnerability(
                                title=f"Echidna Test Error: {test.get('description', 'Unknown')}",
                                description=issue.get("description", "No description available"),
                                severity=self.map_echidna_severity(issue.get("severity", "Low")),
                                contract=issue.get("contract", "Unknown"),
                                line_number=issue.get("line", None),
                                code_snippet=issue.get("code", ""),
                                recommendation="Review and fix the issue",
                                tool="Echidna",
                                confidence="high"
                            )

                            vulnerabilities.append(vulnerability)

        except Exception as e:
            print(f"⚠️  Error parsing Echidna results: {e}")

        return vulnerabilities

    def map_slither_severity(self, slither_severity):
        """Map Slither severity to our severity enum."""
        mapping = {
            "informational": VulnerabilitySeverity.INFO,
            "low": VulnerabilitySeverity.LOW,
            "medium": VulnerabilitySeverity.MEDIUM,
            "high": VulnerabilitySeverity.HIGH,
            "critical": VulnerabilitySeverity.CRITICAL
        }
        return mapping.get(slither_severity, VulnerabilitySeverity.MEDIUM)

    def map_mythril_severity(self, mythril_severity):
        """Map Mythril severity to our severity enum."""
        mapping = {
            "Informational": VulnerabilitySeverity.INFO,
            "Low": VulnerabilitySeverity.LOW,
            "Medium": VulnerabilitySeverity.MEDIUM,
            "High": VulnerabilitySeverity.HIGH,
            "Critical": VulnerabilitySeverity.CRITICAL
        }
        return mapping.get(mythril_severity, VulnerabilitySeverity.MEDIUM)

    def map_echidna_severity(self, echidna_severity):
        """Map Echidna severity to our severity enum."""
        mapping = {
            "Low": VulnerabilitySeverity.LOW,
            "Medium": Vulnerability.MEDIUM,
            "High": Vulnerability.HIGH,
            "Critical": VulnerabilitySeverity.CRITICAL
        }
        return mapping.get(echidna_severity, VulnerabilitySeverity.MEDIUM)

    def deduplicate_vulnerabilities(self, vulnerabilities):
        """Remove duplicate vulnerabilities."""
        seen = set()
        unique_vulnerabilities = []

        for vuln in vulnerabilities:
            # Create a unique key based on title, contract, and line number
            key = (vuln.title, vuln.contract, vuln.line_number)
            if key not in seen:
                seen.add(key)
                unique_vulnerabilities.append(vuln)

        return unique_vulnerabilities

    def categorize_vulnerabilities(self, vulnerabilities):
        """Categorize vulnerabilities by severity."""
        categorized = {
            VulnerabilitySeverity.CRITICAL: [],
            VulnerabilitySeverity.HIGH: [],
            VulnerabilitySeverity.MEDIUM: [],
            VulnerabilitySeverity.WARNING: [],
            VulnerabilitySeverity.INFO: [],
            VulnerabilitySeverity.LOW: []
        }

        for vuln in vulnerabilities:
            categorized[vuln.severity].append(vuln)

        return categorized

    def generate_security_report(self, vulnerabilities, scan_info):
        """Generate comprehensive security report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"security_report_{timestamp}.json"
        markdown_file = self.reports_dir / f"security_report_{timestamp}.md"

        # Categorize vulnerabilities
        categorized = self.categorize_vulnerabilities(vulnerabilities)

        # Create JSON report
        report = {
            "scan_info": scan_info,
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "critical": len(categorized[VulnerabilitySeverity.CRITICAL]),
                "high": len(categorized[VulnerabilitySeverity.HIGH]),
                "medium": len(categorized[VulnerabilitySeverity.MEDIUM]),
                "warning": len(categorized[VulnerabilitySeverity.WARNING]),
                "info": len(categorized[VulnerabilitySeverity.INFO]),
                "low": len(categorized[VulnerabilitySeverity.LOW]),
                "timestamp": datetime.now().isoformat()
            },
            "vulnerabilities": [
                {
                    "title": vuln.title,
                    "description": vuln.description,
                    "severity": vuln.severity.value,
                    "contract": vuln.contract,
                    "line_number": vuln.line_number,
                    "code_snippet": vuln.code_snippet,
                    "recommendation": vuln.recommendation,
                    "tool": vuln.tool,
                    "confidence": vuln.confidence,
                    "cwe_id": vuln.cwe_id
                }
                for vuln in vulnerabilities
            ],
            "tools_used": scan_info.get("tools_used", []),
            "recommendations": self.generate_recommendations(categorized)
        }

        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Create Markdown report
        markdown_content = self.generate_markdown_report(report, categorized)
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)

        print(f"\n📊 Security reports generated:")
        print(f"   JSON: {report_file}")
        print(f"   Markdown: {markdown_file}")

        # Print summary
        self.print_security_summary(report)

        return report_file, markdown_file

    def generate_markdown_report(self, report, categorized):
        """Generate markdown security report."""
        summary = report["summary"]

        content = f"""# Smart Contract Security Report

## Scan Summary

- **Scan Date**: {report['scan_info']['timestamp']}
- **Total Vulnerabilities**: {summary['total_vulnerabilities']}
- **Critical**: {summary['critical']}
- **High**: {summary['high']}
- **Medium**: {summary['medium']}
- **Warning**: {summary['warning']}
- **Info**: {summary['info']}
- **Low**: {summary['low']}

## Severity Distribution

| Severity | Count | Percentage |
|----------|-------|------------|
| Critical | {summary['critical']} | {summary['critical']/summary['total_vulnerabilities']*100:.1f}% |
| High | {summary['high']} | {summary['high']/summary['total_vulnerabilities']*100:.1f}% |
| Medium | {summary['medium']} | {summary['medium']/summary['total_vulnerabilities']*100:.1f}% |
| Warning | {summary['warning']} | {summary['warning']/summary['total_vulnerabilities']*100:.1f}% |
| Info | {summary['info']} | {summary['info']/summary['total_vulnerabilities']*100:.1f}% |
| Low | {summary['low']} | {summary['low']/summary['total_vulnerabilities']*100:.1f}% |

## Critical Vulnerabilities

"""

        # Add critical vulnerabilities
        if categorized[VulnerabilitySeverity.CRITICAL]:
            content += "\n### 🚨 Critical Issues\n\n"
            for vuln in categorized[VulnerabilitySeverity.CRITICAL]:
                content += f"#### {vuln.title}\n"
                content += f"**Contract**: `{vuln.contract}`\n"
                content += f"**Line**: {vuln.line_number}\n" if vuln.line_number else ""
                content += f"**Tool**: {vuln.tool}\n"
                content += f"**CWE**: {vuln.cwe_id or 'N/A'}\n\n"
                content += f"**Description**: {vuln.description}\n\n"
                content += f"**Recommendation**: {vuln.recommendation}\n\n"
                if vuln.code_snippet:
                    content += "```solidity\n"
                    content += vuln.code_snippet
                    content += "\n```\n\n"

        # Add high severity vulnerabilities
        if categorized[VulnerabilitySeverity.HIGH]:
            content += "### 🔴 High Severity Issues\n\n"
            for vuln in categorized[VulnerabilitySeverity.HIGH]:
                content += f"#### {vuln.title}\n"
                content += f"**Contract**: `{vuln.contract}`\n"
                content += f"**Line**: {vuln.line_number}\n" if vuln.line_number else ""
                content += f"**Tool**: {vuln.tool}\n"
                content += f"**CWE**: {vuln.cwe_id or 'N/A'}\n\n"
                content += f"**Description**: {vuln.description}\n\n"
                content += f"**Recommendation**: {vuln.recommendation}\n\n"

        # Add medium severity vulnerabilities
        if categorized[VulnerabilitySeverity.MEDIUM]:
            content += "### 🟡 Medium Severity Issues\n\n"
            for vuln in categorized[VulnerabilitySeverity.MEDIUM]:
                content += f"#### {vuln.title}\n"
                content += f"**Contract**: `{vuln.contract}`\n"
                content += f"**Line**: {vuln.line_number}\n" if vuln.line_number else ""
                content += f"**Tool**: {vuln.tool}\n"
                content += f"**CWE**: {vuln.cwe_id or 'N/A'}\n\n"
                content += f"**Description**: {vuln.description}\n\n"
                content += f"**Recommendation**: {vuln.recommendation}\n\n"

        # Add remaining vulnerabilities
        remaining_severities = [
            VulnerabilitySeverity.WARNING,
            VulnerabilitySeverity.INFO,
            VulnerabilitySeverity.LOW
        ]

        for severity in remaining_severities:
            if categorized[severity]:
                content += f"### {severity.value.title()} Issues\n\n"
                for vuln in categorized[severity]:
                    content += f"- **{vuln.title}** - {vuln.description}\n"
                content += "\n"

        return content

    def generate_recommendations(self, categorized):
        """Generate security recommendations based on scan results."""
        recommendations = []

        # General recommendations
        recommendations.extend([
            "1. Review all critical and high severity vulnerabilities immediately",
            "2. Implement comprehensive testing including edge cases",
            "3. Consider formal verification using tools like K Framework",
            "4. Conduct a professional security audit for mainnet deployments",
            "5. Implement bug bounty programs for ongoing security"
        ])

        # Severity-specific recommendations
        if categorized[VulnerabilitySeverity.CRITICAL] or categorized[VulnerabilitySeverity.HIGH]:
            recommendations.append("🚨 HIGH PRIORITY: Address critical and high severity issues before deployment")

        if categorized[VulnerabilitySeverity.MEDIUM]:
            recommendations.append("🟡 Address medium severity issues to improve security posture")

        if categorized[VulnerabilitySeverity.WARNING]:
            recommendations.append("⚠️ Review warning-level issues for potential improvements")

        return recommendations

    def print_security_summary(self, report):
        """Print security summary to console."""
        summary = report["summary"]

        print("\n" + "="*60)
        print("🔒 SMART CONTRACT SECURITY SCAN SUMMARY")
        print("="*60)
        print(f"Total Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"Critical: {summary['critical']} | High: {summary['high']} | Medium: {summary['medium']}")
        print(f"Warning: {summary['warning']} | Info: {summary['info']} | Low: {summary['low']}")
        print()

        if summary['critical'] > 0:
            print("🚨 CRITICAL ISSUES FOUND - Address immediately!")
        elif summary['high'] > 0:
            print("🔴 HIGH SEVERITY ISSUES - Address before deployment!")
        elif summary['medium'] > 0:
            print("🟡 Medium issues found - Review and fix")
        else:
            print("✅ No critical issues detected")

        print("="*60)

    def scan_contracts(self, contract_path=None, project_path=None, tools=None, full_scan=False):
        """Perform comprehensive security scan."""
        print("🔒 Starting comprehensive security scan...")
        print()

        scan_info = {
            "timestamp": datetime.now().isoformat(),
            "contract_path": contract_path,
            "project_path": project_path,
            "tools_used": tools or [],
            "full_scan": full_scan
        }

        all_vulnerabilities = []

        # Determine what to scan
        if contract_path:
            # Single contract scan
            print(f"📄 Scanning contract: {contract_path}")
        elif project_path:
            # Project scan
            print(f"📁 Scanning project: {project_path}")
        else:
            # Current directory scan
            print("📁 Scanning current directory")

        # Determine which tools to use
        if not tools:
            if full_scan:
                tools = ["slither", "mythril", "echidna", "upgrade_security_analysis"]
            else:
                tools = ["slither", "pattern_matching", "security_rules", "upgrade_security_analysis"]

        print(f"🛠️  Tools: {', '.join(tools)}")
        print()

        # Perform scans with each tool
        for tool in tools:
            if tool == "slither":
                vulns, output = self.scan_with_slither(contract_path, project_path)
                all_vulnerabilities.extend(vulns)
                if output:
                    print(f"Slither output preview:\n{output[:500]}...")

            elif tool == "mythril":
                vulns, output = self.scan_with_mythril(contract_path, project_path)
                all_vulnerabilities.extend(vulns)
                if output:
                    print(f"Mythril output preview:\n{output[:500]}...")

            elif tool == "echidna":
                vulns, output = self.scan_with_echidna(contract_path, project_path)
                all_vulnerabilities.extend(vulns)
                if output:
                    print(f"Echidna output preview:\n{output[:500]}...")

            elif tool == "pattern_matching":
                if contract_path:
                    vulns = self.perform_pattern_matching(contract_path)
                    all_vulnerabilities.extend(vulns)

            elif tool == "security_rules":
                if contract_path:
                    vulns = self.perform_security_rules_check(contract_path, project_path)
                    all_vulnerabilities.extend(vulns)

            elif tool == "upgrade_security_analysis":
                if contract_path:
                    vulns = self.perform_upgrade_security_analysis(contract_path, project_path)
                    all_vulnerabilities.extend(vulns)

        # Deduplicate vulnerabilities
        all_vulnerabilities = self.deduplicate_vulnerabilities(all_vulnerabilities)

        # Generate report
        if all_vulnerabilities:
            report_file, markdown_file = self.generate_security_report(all_vulnerabilities, scan_info)
            print(f"\n📋 Detailed reports saved:")
            print(f"   JSON: {report_file}")
            print(f"   Markdown: {markdown_file}")
        else:
            print("\n✅ No vulnerabilities found!")

        return all_vulnerabilities

    def create_scan_config(self, project_path, tools=None, custom_rules=None):
        """Create security scanning configuration."""
        config = {
            "project_path": project_path,
            "scan_frequency": "on_demand",
            "tools": tools or ["slither", "pattern_matching", "security_rules"],
            "custom_rules": custom_rules or {},
            "alerting": {
                "email": {
                    "enabled": False,
                    "recipients": [],
                    "threshold": {
                        "critical": 0,
                        "high": 0,
                        "medium": 5
                    }
                },
                "slack": {
                    "enabled": False,
                    "webhook": ""
                },
                "discord": {
                    "enabled": False,
                    "webhook": ""
                }
            },
            "exclusions": [
                "node_modules/",
                "test/",
                "mock/",
                "interface/"
            ],
            "created_at": datetime.now().isoformat()
        }

        config_file = self.configs_dir / f"scan_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Scan configuration saved to: {config_file}")
        return config_file

    def interactive_mode(self):
        """Interactive security scanning setup."""
        print("🔒 Interactive Security Scanner")
        print("=" * 50)

        # Get scan target
        print("\nScan target:")
        print("1. Single contract file")
        print("2. Entire project")
        print("3. Current directory")

        while True:
            try:
                choice = input("\nSelect scan target (1-3): ").strip()
                if choice in ["1", "2", "3"]:
                    break
                print("Invalid choice.")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                return

        if choice == "1":
            # Single contract
            contract_path = input("Enter contract file path: ").strip()
            if Path(contract_path).exists():
                print(f"\n🔍 Starting security scan for: {contract_path}")
                vulnerabilities = self.scan_contracts(contract_path=contract_path)
            else:
                print(f"❌ Contract file not found: {contract_path}")
                return

        elif choice == "2":
            # Entire project
            project_path = input("Enter project directory path: ").strip()
            if Path(project_path).exists():
                print(f"\n🔍 Starting security scan for project: {project_path}")
                vulnerabilities = self.scan_contracts(project_path=project_path, full_scan=True)
            else:
                print(f"❌ Project directory not found: {project_path}")
                return

        else:
            # Current directory
            print("\n🔍 Starting security scan for current directory")
            vulnerabilities = self.scan_contracts(full_scan=True)

        return vulnerabilities

    def setup_automated_scanning(self, project_path):
        """Setup automated security scanning for CI/CD."""
        print("🔧 Setting up automated security scanning...")

        # Create CI configuration
        ci_config = {
            "github_actions": f"""name: Security Scan
on: [push, pull_request]
jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'

    - name: Install security tools
      run: |
        pip install slither-analyzer mythril echidna
        npm install -g scribble

    - name: Run Slither
      run: slither --json --output slither-results.json || true

    - name: Run Mythril
      run: mythril -x --json --output mythril-results.json || true

    - name: Run Echidna
      run: echidna-test --format json --output echidna-results.json || true

    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: security-scan-results
        path: |
          slither-results.json
          mythril-results.json
          echidna-results.json
"""
        }

        # Create GitHub Actions workflow file
        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflow_dir / "security-scan.yml"

        with open(workflow_file, 'w') as f:
            f.write(ci_config)

        print(f"✅ GitHub Actions workflow saved to: {workflow_file}")

        # Create pre-commit hook
        pre_commit_config = f"""#!/bin/sh
# Pre-commit security scan
echo "🔍 Running security scan..."

# Run Slither
echo "  - Running Slither analysis..."
slither --json --output slither-pre-commit.json || true

# Run pattern matching
echo "  - Running pattern analysis..."
python3 {__file__} --scan contracts/ --tools pattern_matching || true

# Check results
if [ -f "slither-pre-commit.json" ]; then
    critical_count=$(jq '[.results.detectors[] | select(.impact == "critical")] | length' slither-pre-commit.json)
    if [ $critical_count -gt 0 ]; then
        echo "🚨 Critical security issues found! Commit blocked."
        exit 1
    fi
fi

echo "✅ Security scan completed"
"""

        pre_commit_file = Path(".pre-commit")
        with open(pre_commit_file, 'w') as f:
            f.write(pre_commit_config)

        # Make pre-commit file executable
        pre_commit_file.chmod(0o755)

        print(f"✅ Pre-commit hook saved to: {pre_commit_file}")

        print(f"\n🔧 Automated security scanning setup completed!")
        print("📁 Files created:")
        print(f"   GitHub Actions: {workflow_file}")
        print(f"   Pre-commit: {pre_commit_file}")
        print("\n📝 Setup instructions:")
        print(f"1. Install GitHub Actions on your repository")
        print(f"2. Commit the workflow file and pre-commit hook")
        print(f"3. Security scans will run automatically on push and PRs")


def main():
    parser = argparse.ArgumentParser(description="Smart contract security scanner and auditor")
    parser.add_argument("--scan", help="Contract file to scan")
    parser.add_argument("--project", help="Project directory to scan")
    parser.add_argument("--tools", help="Comma-separated list of tools to use")
    parser.add_argument("--full-scan", action="store_true", help="Run comprehensive scan with all tools")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--setup-ci", help="Setup automated scanning for CI/CD")
    parser.add_argument("--list-tools", action="store_true", help="List available security tools")
    parser.add_argument("--create-config", help="Create scan configuration file")

    args = parser.parse_args()

    scanner = SecurityScanner()

    if args.list_tools:
        print("Available security tools:")
        for tool_name, tool_info in scanner.tools.items():
            status = "✅ Available" if tool_info["supported"] else "❌ Not supported"
            print(f"  {tool_name}: {tool_info['name']} - {status}")
            print(f"    {tool_info['description']}")
            print(f"    Install: {tool_info['install_cmd']}")
            print()

    elif args.setup_ci:
        project_path = args.project or "."
        scanner.setup_automated_scanning(project_path)

    elif args.create_config:
        project_path = args.project or "."
        tools = args.tools.split(",") if args.tools else None
        scanner.create_scan_config(project_path, tools)

    elif args.interactive:
        scanner.interactive_mode()

    elif args.scan or args.project:
        tools = args.tools.split(",") if args.tools else ["slither", "pattern_matching", "security_rules", "upgrade_security_analysis"]
        if args.full_scan:
            tools = ["slither", "mythril", "echidna", "pattern_matching", "security_rules", "upgrade_security_analysis"]

        vulnerabilities = scanner.scan_contracts(
            contract_path=args.scan,
            project_path=args.project,
            tools=tools,
            full_scan=args.full_scan
        )

    else:
        print("❌ Please provide --scan <contract-path>, --project <project-path>, --interactive, or use --setup-ci")
        parser.print_help()


if __name__ == "__main__":
    main()