"""
Security utilities for code safety scanning and validation.
"""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CodeSafetyScanner:
    """Scans generated code for potential security risks."""
    
    def __init__(self):
        """Initialize the security scanner."""
        self.dangerous_patterns = {
            "file_operations": [
                r"open\s*\([^)]*['\"]\/[^'\"]*['\"]",  # File operations with absolute paths
                r"os\.remove\s*\(",                    # File deletion
                r"os\.rmdir\s*\(",                     # Directory deletion
                r"shutil\.rmtree\s*\(",                # Recursive deletion
                r"os\.system\s*\(",                    # System command execution
                r"subprocess\.(run|call|Popen)",       # Process execution
                r"eval\s*\(",                          # Code evaluation
                r"exec\s*\(",                          # Code execution
            ],
            "network_operations": [
                r"socket\.",                           # Socket operations
                r"urllib\.request",                    # HTTP requests
                r"requests\.(get|post|put|delete)",    # HTTP requests
                r"http\.client",                       # HTTP client
                r"ftplib\.",                           # FTP operations
            ],
            "dangerous_imports": [
                r"import\s+os",                        # OS operations
                r"import\s+sys",                       # System operations
                r"import\s+subprocess",                # Process control
                r"import\s+pickle",                    # Serialization (can execute code)
                r"from\s+os\s+import",                 # OS operations
                r"from\s+subprocess\s+import",         # Process control
            ],
            "data_access": [
                r"sqlite3\.",                          # Database operations
                r"psycopg2\.",                         # PostgreSQL
                r"mysql\.",                            # MySQL operations
                r"mongodb\.",                          # MongoDB operations
            ]
        }
        
        self.severity_levels = {
            "file_operations": "HIGH",
            "network_operations": "MEDIUM", 
            "dangerous_imports": "MEDIUM",
            "data_access": "LOW"
        }
    
    def scan_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Scan code for security vulnerabilities.
        
        Args:
            code: Code to scan
            language: Programming language
        
        Returns:
            Scan results with identified risks
        """
        if language.lower() != "python":
            # For non-Python code, perform basic scanning
            return self._scan_generic_code(code, language)
        
        risks = []
        risk_score = 0
        
        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
                if matches:
                    severity = self.severity_levels.get(category, "LOW")
                    risk = {
                        "category": category,
                        "pattern": pattern,
                        "matches": matches,
                        "severity": severity,
                        "description": self._get_risk_description(category)
                    }
                    risks.append(risk)
                    
                    # Add to risk score
                    score_map = {"HIGH": 10, "MEDIUM": 5, "LOW": 2}
                    risk_score += score_map.get(severity, 1) * len(matches)
        
        # Determine overall safety level
        if risk_score >= 20:
            safety_level = "DANGEROUS"
        elif risk_score >= 10:
            safety_level = "MODERATE_RISK"
        elif risk_score >= 5:
            safety_level = "LOW_RISK"
        else:
            safety_level = "SAFE"
        
        return {
            "language": language,
            "safety_level": safety_level,
            "risk_score": risk_score,
            "risks": risks,
            "scan_timestamp": self._get_timestamp()
        }
    
    def _scan_generic_code(self, code: str, language: str) -> Dict[str, Any]:
        """Scan non-Python code for basic security patterns."""
        risks = []
        risk_score = 0
        
        # Generic dangerous patterns
        generic_patterns = {
            "system_calls": [
                r"system\s*\(",                       # System calls
                r"exec\s*\(",                         # Execution
                r"shell_exec\s*\(",                   # Shell execution (PHP)
                r"Runtime\.getRuntime\(\)\.exec",     # Java execution
            ],
            "file_operations": [
                r"File\s*\(",                         # File operations
                r"FileReader\s*\(",                   # File reading
                r"FileWriter\s*\(",                   # File writing
                r"delete\s*\(",                       # File deletion
            ]
        }
        
        for category, patterns in generic_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    risk = {
                        "category": category,
                        "pattern": pattern,
                        "matches": matches,
                        "severity": "MEDIUM",
                        "description": f"Potentially dangerous {category} detected"
                    }
                    risks.append(risk)
                    risk_score += 5 * len(matches)
        
        safety_level = "MODERATE_RISK" if risks else "SAFE"
        
        return {
            "language": language,
            "safety_level": safety_level,
            "risk_score": risk_score,
            "risks": risks,
            "scan_timestamp": self._get_timestamp()
        }
    
    def _get_risk_description(self, category: str) -> str:
        """Get description for risk category."""
        descriptions = {
            "file_operations": "Code performs file system operations that could modify or delete files",
            "network_operations": "Code makes network requests that could access external resources",
            "dangerous_imports": "Code imports modules that provide system-level access",
            "data_access": "Code accesses databases or external data sources"
        }
        return descriptions.get(category, "Unknown security risk")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def is_code_safe(self, scan_result: Dict[str, Any]) -> bool:
        """
        Determine if code is safe to execute.
        
        Args:
            scan_result: Result from scan_code()
        
        Returns:
            True if code is considered safe
        """
        return scan_result.get("safety_level") in ["SAFE", "LOW_RISK"]


class InputValidator:
    """Validates user input for security."""
    
    @staticmethod
    def validate_code_requirements(requirements: str) -> Dict[str, Any]:
        """
        Validate code generation requirements.
        
        Args:
            requirements: User requirements
        
        Returns:
            Validation result
        """
        issues = []
        
        # Check for suspicious requests
        suspicious_patterns = [
            r"hack",
            r"exploit",
            r"vulnerability",
            r"backdoor",
            r"malware",
            r"virus",
            r"keylogger",
            r"password\s+crack",
            r"steal\s+data",
            r"bypass\s+security"
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, requirements, re.IGNORECASE):
                issues.append(f"Potentially malicious request detected: {pattern}")
        
        # Check length
        if len(requirements) > 5000:
            issues.append("Requirements too long")
        
        if len(requirements) < 10:
            issues.append("Requirements too short")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input.
        
        Args:
            text: Input text
        
        Returns:
            Sanitized text
        """
        # Remove potentially dangerous characters
        sanitized = re.sub(r"[<>\"'&]", "", text)
        
        # Limit length
        if len(sanitized) > 5000:
            sanitized = sanitized[:5000]
        
        return sanitized.strip()


# Global scanner instance
_security_scanner: Optional[CodeSafetyScanner] = None


def get_security_scanner() -> CodeSafetyScanner:
    """Get the global security scanner instance."""
    global _security_scanner
    if _security_scanner is None:
        _security_scanner = CodeSafetyScanner()
    return _security_scanner