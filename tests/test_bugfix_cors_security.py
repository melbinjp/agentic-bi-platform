"""
Bug Condition Exploration Test - CORS Security Vulnerability

**Validates: Requirements 1.5, 1.6, 1.7**

This test explores the bug condition where CORS middleware is configured with
wildcard allow_methods=["*"] and allow_headers=["*"] combined with allow_credentials=True,
creating a security anti-pattern that allows dangerous HTTP methods and arbitrary headers.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected Outcome: Test FAILS with counterexample showing wildcards in CORS configuration.
"""

import pytest
import ast
from pathlib import Path
from fastapi.testclient import TestClient
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_bug_condition_cors_security_vulnerability_static_analysis():
    """
    Property 1: Bug Condition - CORS Security Vulnerability (Static Analysis)
    
    **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Bug Condition: CORS configured with wildcards ["*"] for methods/headers + allow_credentials=True
    
    This test uses static code analysis to detect the bug pattern without
    needing to execute the code or deal with import dependencies.
    
    Expected on UNFIXED code: Test FAILS - finds wildcards in CORS configuration
    Expected on FIXED code: Test PASSES - CORS restricted to specific methods/headers
    """
    
    # Read the main.py file
    main_path = Path(__file__).parent.parent / "app" / "main.py"
    
    assert main_path.exists(), f"Main file not found at {main_path}"
    
    with open(main_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Parse the AST
    tree = ast.parse(source_code)
    
    # Find the CORS middleware configuration
    bug_found = False
    bug_details = {
        "wildcard_methods": False,
        "wildcard_headers": False,
        "allow_credentials": False,
        "location": None
    }
    
    class CORSConfigVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            nonlocal bug_found, bug_details
            
            # Check if this is app.add_middleware call
            if (isinstance(node.func, ast.Attribute) and 
                node.func.attr == "add_middleware"):
                
                # Check if it's CORSMiddleware
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id == "CORSMiddleware":
                        # Found CORS middleware configuration
                        # Check the keyword arguments
                        for keyword in node.keywords:
                            if keyword.arg == "allow_methods":
                                # Check if it's a list containing "*"
                                if isinstance(keyword.value, ast.List):
                                    for elt in keyword.value.elts:
                                        if isinstance(elt, ast.Constant) and elt.value == "*":
                                            bug_details["wildcard_methods"] = True
                                            bug_details["location"] = node.lineno
                            
                            elif keyword.arg == "allow_headers":
                                # Check if it's a list containing "*"
                                if isinstance(keyword.value, ast.List):
                                    for elt in keyword.value.elts:
                                        if isinstance(elt, ast.Constant) and elt.value == "*":
                                            bug_details["wildcard_headers"] = True
                                            if not bug_details["location"]:
                                                bug_details["location"] = node.lineno
                            
                            elif keyword.arg == "allow_credentials":
                                # Check if it's True
                                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                    bug_details["allow_credentials"] = True
            
            self.generic_visit(node)
    
    visitor = CORSConfigVisitor()
    visitor.visit(tree)
    
    # Bug exists if wildcards are present with allow_credentials=True
    if (bug_details["wildcard_methods"] or bug_details["wildcard_headers"]) and bug_details["allow_credentials"]:
        bug_found = True
    
    # Generate counterexample if bug found
    if bug_found:
        counterexample = {
            "bug_condition": "CORS Security Vulnerability",
            "details": bug_details,
            "formal_spec": "isBugCondition3(cors_config) = TRUE",
            "explanation": (
                "The CORS middleware is configured with wildcard allow_methods=['*'] and/or "
                "allow_headers=['*'] combined with allow_credentials=True. "
                "This creates a security anti-pattern that allows dangerous HTTP methods "
                "(DELETE, PUT, PATCH) and arbitrary headers from any origin, potentially "
                "exposing credentials to attacks."
            ),
            "expected_fix": (
                'allow_methods=["GET", "POST"],\n'
                'allow_headers=["Content-Type", "X-API-Key"]'
            ),
            "current_code": (
                f'allow_methods=["*"],  # Line ~{bug_details["location"]}\n'
                f'allow_headers=["*"],\n'
                f'allow_credentials=True'
            )
        }
        
        vulnerabilities = []
        if bug_details["wildcard_methods"]:
            vulnerabilities.append("✓ Wildcard methods ['*'] allows DELETE, PUT, PATCH")
        if bug_details["wildcard_headers"]:
            vulnerabilities.append("✓ Wildcard headers ['*'] allows arbitrary headers")
        if bug_details["allow_credentials"]:
            vulnerabilities.append("✓ allow_credentials=True with wildcards is dangerous")
        
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG DETECTED: CORS Security Vulnerability\n"
            f"{'='*80}\n\n"
            f"Counterexample:\n"
            f"  Location: main.py line ~{bug_details['location']}\n"
            f"  Wildcard Methods: {bug_details['wildcard_methods']}\n"
            f"  Wildcard Headers: {bug_details['wildcard_headers']}\n"
            f"  Allow Credentials: {bug_details['allow_credentials']}\n\n"
            f"Formal Specification:\n"
            f"  isBugCondition3(cors_config) = TRUE\n"
            f"  WHERE:\n"
            f"    - ('*' IN cors_config.allow_methods OR '*' IN cors_config.allow_headers)\n"
            f"    - cors_config.allow_credentials == True\n\n"
            f"Security Vulnerabilities:\n"
            f"  " + "\n  ".join(vulnerabilities) + "\n\n"
            f"Violation:\n"
            f"  {counterexample['explanation']}\n\n"
            f"Current Code (INSECURE):\n"
            f"  {counterexample['current_code']}\n\n"
            f"Expected Code (SECURE):\n"
            f"  {counterexample['expected_fix']}\n\n"
            f"Attack Scenarios:\n"
            f"  1. DELETE requests from malicious origins can delete resources\n"
            f"  2. PUT requests can modify data without proper CORS restrictions\n"
            f"  3. Arbitrary headers like X-Malicious-Header can bypass security\n"
            f"  4. Credentials exposed to any origin with wildcard configuration\n\n"
            f"This test MUST FAIL on unfixed code to confirm the bug exists.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug is fixed
    assert not bug_found, (
        "Bug should be fixed: CORS should restrict methods to ['GET', 'POST'] "
        "and headers to ['Content-Type', 'X-API-Key'], not use wildcards."
    )


def test_bug_condition_cors_allows_dangerous_methods():
    """
    Verify that CORS configuration allows dangerous HTTP methods
    
    This test confirms that the current CORS configuration allows
    DELETE, PUT, and PATCH methods, which should be restricted.
    """
    
    from app.main import app
    client = TestClient(app)
    
    # Test that dangerous methods are allowed by CORS
    dangerous_methods = ["DELETE", "PUT", "PATCH", "OPTIONS"]
    
    allowed_methods = []
    for method in dangerous_methods:
        # Send a preflight request
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        # Check if the method is allowed
        if response.status_code == 200:
            allowed_header = response.headers.get("access-control-allow-methods", "")
            if "*" in allowed_header or method in allowed_header:
                allowed_methods.append(method)
    
    if allowed_methods:
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG CONFIRMED: CORS Allows Dangerous HTTP Methods\n"
            f"{'='*80}\n\n"
            f"Dangerous Methods Allowed:\n"
            f"  " + "\n  ".join(allowed_methods) + "\n\n"
            f"Security Impact:\n"
            f"  - DELETE: Can delete resources from any origin\n"
            f"  - PUT: Can modify data from any origin\n"
            f"  - PATCH: Can partially update data from any origin\n\n"
            f"Current Configuration:\n"
            f"  allow_methods=['*']  # Allows ALL methods including dangerous ones\n\n"
            f"Expected Configuration:\n"
            f"  allow_methods=['GET', 'POST']  # Only safe methods\n\n"
            f"This confirms the CORS security vulnerability exists.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, dangerous methods are not allowed
    assert len(allowed_methods) == 0, "Dangerous methods should not be allowed"


def test_bug_condition_cors_allows_arbitrary_headers():
    """
    Verify that CORS configuration allows arbitrary headers
    
    This test confirms that the current CORS configuration allows
    any custom headers, which could bypass security controls.
    """
    
    from app.main import app
    client = TestClient(app)
    
    # Test that arbitrary headers are allowed by CORS
    arbitrary_headers = [
        "X-Malicious-Header",
        "X-Custom-Auth",
        "X-Bypass-Security",
        "X-Admin-Override"
    ]
    
    allowed_headers = []
    for header in arbitrary_headers:
        # Send a preflight request
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": header.lower()
            }
        )
        
        # Check if the header is allowed
        if response.status_code == 200:
            allowed_header = response.headers.get("access-control-allow-headers", "")
            if "*" in allowed_header or header.lower() in allowed_header.lower():
                allowed_headers.append(header)
    
    if allowed_headers:
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG CONFIRMED: CORS Allows Arbitrary Headers\n"
            f"{'='*80}\n\n"
            f"Arbitrary Headers Allowed:\n"
            f"  " + "\n  ".join(allowed_headers) + "\n\n"
            f"Security Impact:\n"
            f"  - Arbitrary headers can bypass security controls\n"
            f"  - Malicious headers can be injected from any origin\n"
            f"  - Custom authentication headers can be spoofed\n"
            f"  - Admin override headers can escalate privileges\n\n"
            f"Current Configuration:\n"
            f"  allow_headers=['*']  # Allows ALL headers including malicious ones\n\n"
            f"Expected Configuration:\n"
            f"  allow_headers=['Content-Type', 'X-API-Key']  # Only necessary headers\n\n"
            f"This confirms the CORS security vulnerability exists.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, arbitrary headers are not allowed
    assert len(allowed_headers) == 0, "Arbitrary headers should not be allowed"


def test_bug_condition_formal_specification_check():
    """
    Formal specification verification using pattern matching
    
    FUNCTION isBugCondition3(cors_config)
      INPUT: cors_config of type CORSMiddlewareConfig
      OUTPUT: boolean
      
      RETURN ("*" IN cors_config.allow_methods OR "*" IN cors_config.allow_headers)
             AND cors_config.allow_credentials == True
    END FUNCTION
    """
    
    main_path = Path(__file__).parent.parent / "app" / "main.py"
    
    with open(main_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Pattern matching for the bug
    import re
    
    # Look for CORS configuration with wildcards
    # Pattern 1: allow_methods=["*"]
    methods_pattern = r'allow_methods\s*=\s*\[\s*["\']?\*["\']?\s*\]'
    
    # Pattern 2: allow_headers=["*"]
    headers_pattern = r'allow_headers\s*=\s*\[\s*["\']?\*["\']?\s*\]'
    
    # Pattern 3: allow_credentials=True
    credentials_pattern = r'allow_credentials\s*=\s*True'
    
    methods_matches = list(re.finditer(methods_pattern, source_code))
    headers_matches = list(re.finditer(headers_pattern, source_code))
    credentials_matches = list(re.finditer(credentials_pattern, source_code))
    
    has_wildcard_methods = len(methods_matches) > 0
    has_wildcard_headers = len(headers_matches) > 0
    has_credentials = len(credentials_matches) > 0
    
    if (has_wildcard_methods or has_wildcard_headers) and has_credentials:
        # Find line numbers
        methods_line = source_code[:methods_matches[0].start()].count('\n') + 1 if methods_matches else None
        headers_line = source_code[:headers_matches[0].start()].count('\n') + 1 if headers_matches else None
        credentials_line = source_code[:credentials_matches[0].start()].count('\n') + 1 if credentials_matches else None
        
        pytest.fail(
            f"\n{'='*80}\n"
            f"FORMAL SPECIFICATION VIOLATION DETECTED\n"
            f"{'='*80}\n\n"
            f"isBugCondition3(cors_config) = TRUE\n\n"
            f"Counterexample:\n"
            f"  Wildcard Methods: {has_wildcard_methods} (line {methods_line})\n"
            f"  Wildcard Headers: {has_wildcard_headers} (line {headers_line})\n"
            f"  Allow Credentials: {has_credentials} (line {credentials_line})\n\n"
            f"Formal Specification Check:\n"
            f"  {'✓' if has_wildcard_methods else '✗'} '*' IN cors_config.allow_methods\n"
            f"  {'✓' if has_wildcard_headers else '✗'} '*' IN cors_config.allow_headers\n"
            f"  ✓ cors_config.allow_credentials == True\n\n"
            f"Result: Bug condition is TRUE - bug exists in the code.\n\n"
            f"This confirms the CORS configuration has a security anti-pattern:\n"
            f"  - Wildcards with allow_credentials=True expose credentials to attacks\n"
            f"  - Dangerous methods (DELETE, PUT, PATCH) are allowed from any origin\n"
            f"  - Arbitrary headers can bypass security controls\n\n"
            f"Expected Behavior:\n"
            f"  CORS should be restricted to:\n"
            f"    allow_methods=['GET', 'POST']\n"
            f"    allow_headers=['Content-Type', 'X-API-Key']\n"
            f"    allow_credentials=True  # Safe with explicit allowlists\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug is fixed
    assert not ((has_wildcard_methods or has_wildcard_headers) and has_credentials), (
        "Bug should be fixed: CORS should not use wildcards with allow_credentials=True"
    )


def test_bug_condition_line_47_48_verification():
    """
    Direct verification of lines 47-48 in main.py where CORS wildcards exist
    
    This test specifically checks lines 47-48 where the bug is documented to exist.
    """
    
    main_path = Path(__file__).parent.parent / "app" / "main.py"
    
    with open(main_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    bug_lines = []
    
    # Check line 47 (0-indexed, so line 46)
    if len(lines) >= 47:
        line_47 = lines[46].strip()
        if "allow_methods" in line_47 and "*" in line_47:
            bug_lines.append(("Line 47", line_47, "Wildcard methods"))
    
    # Check line 48 (0-indexed, so line 47)
    if len(lines) >= 48:
        line_48 = lines[47].strip()
        if "allow_headers" in line_48 and "*" in line_48:
            bug_lines.append(("Line 48", line_48, "Wildcard headers"))
    
    if bug_lines:
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG CONFIRMED AT LINES 47-48\n"
            f"{'='*80}\n\n"
            f"Bug Lines Found:\n" +
            "\n".join([f"  {loc}: {code}\n    Issue: {issue}" for loc, code, issue in bug_lines]) +
            f"\n\n"
            f"These lines configure CORS with wildcards, creating security vulnerabilities:\n"
            f"  - allow_methods=['*'] allows DELETE, PUT, PATCH from any origin\n"
            f"  - allow_headers=['*'] allows arbitrary headers that can bypass security\n\n"
            f"Expected fix:\n"
            f"  Line 47: allow_methods=['GET', 'POST'],\n"
            f"  Line 48: allow_headers=['Content-Type', 'X-API-Key'],\n\n"
            f"Security Impact:\n"
            f"  - Dangerous HTTP methods can modify/delete data\n"
            f"  - Arbitrary headers can bypass authentication/authorization\n"
            f"  - Credentials exposed to potential attacks\n\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, lines 47-48 don't have the bug pattern
    assert len(bug_lines) == 0, "Lines 47-48 should be fixed"


def test_bug_condition_security_impact_demonstration():
    """
    Demonstrate the security impact of wildcard CORS configuration
    
    This test shows concrete examples of how the bug enables attacks.
    """
    
    from app.main import app
    client = TestClient(app)
    
    security_issues = []
    
    # Test 1: DELETE method allowed
    response = client.options(
        "/api/v1/jobs/test-job-id",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    
    if response.status_code == 200:
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        if "*" in allowed_methods or "DELETE" in allowed_methods:
            security_issues.append({
                "issue": "DELETE method allowed from malicious origin",
                "impact": "Attacker can delete jobs/resources",
                "example": "DELETE /api/v1/jobs/{job_id} from http://malicious-site.com"
            })
    
    # Test 2: Arbitrary header allowed
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-admin-override"
        }
    )
    
    if response.status_code == 200:
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        if "*" in allowed_headers:
            security_issues.append({
                "issue": "Arbitrary headers allowed from malicious origin",
                "impact": "Attacker can inject custom headers to bypass security",
                "example": "POST with X-Admin-Override header from http://malicious-site.com"
            })
    
    # Test 3: PUT method allowed
    response = client.options(
        "/api/v1/jobs/test-job-id",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    
    if response.status_code == 200:
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        if "*" in allowed_methods or "PUT" in allowed_methods:
            security_issues.append({
                "issue": "PUT method allowed from malicious origin",
                "impact": "Attacker can modify job data",
                "example": "PUT /api/v1/jobs/{job_id} from http://malicious-site.com"
            })
    
    if security_issues:
        pytest.fail(
            f"\n{'='*80}\n"
            f"SECURITY IMPACT DEMONSTRATED: {len(security_issues)} Attack Vectors Found\n"
            f"{'='*80}\n\n" +
            "\n\n".join([
                f"Attack Vector {i+1}:\n"
                f"  Issue: {issue['issue']}\n"
                f"  Impact: {issue['impact']}\n"
                f"  Example: {issue['example']}"
                for i, issue in enumerate(security_issues)
            ]) +
            f"\n\n"
            f"Root Cause:\n"
            f"  CORS configured with wildcards:\n"
            f"    allow_methods=['*']\n"
            f"    allow_headers=['*']\n"
            f"    allow_credentials=True\n\n"
            f"This combination creates a security anti-pattern that allows:\n"
            f"  1. Dangerous HTTP methods from any origin\n"
            f"  2. Arbitrary headers that can bypass security controls\n"
            f"  3. Credentials exposed to potential attacks\n\n"
            f"Expected Configuration:\n"
            f"  allow_methods=['GET', 'POST']  # Only safe methods\n"
            f"  allow_headers=['Content-Type', 'X-API-Key']  # Only necessary headers\n"
            f"  allow_credentials=True  # Safe with explicit allowlists\n\n"
            f"This demonstrates the real-world security impact of the bug.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the security issues are fixed
    assert len(security_issues) == 0, "Security vulnerabilities should be fixed"
