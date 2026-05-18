"""
Bug Condition Exploration Test - Orchestrator Database Coupling

**Validates: Requirements 1.1, 1.2**

This test explores the bug condition where the orchestrator passes the database
session directly to the research agent, violating the blackboard pattern architecture.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected Outcome: Test FAILS with counterexample showing "db" in research.run arguments.
"""

import pytest
import ast
import os
from pathlib import Path


def test_bug_condition_orchestrator_database_coupling_static_analysis():
    """
    Property 1: Bug Condition - Orchestrator Database Coupling Violation (Static Analysis)
    
    **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Bug Condition: orchestrator.run() passes db session to research.run()
    
    This test uses static code analysis to detect the bug pattern without
    needing to execute the code or deal with import dependencies.
    
    Expected on UNFIXED code: Test FAILS - finds "db": db in research.run call
    Expected on FIXED code: Test PASSES - no "db" key in research.run call
    """
    
    # Read the orchestrator.py file
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    assert orchestrator_path.exists(), f"Orchestrator file not found at {orchestrator_path}"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Parse the AST
    tree = ast.parse(source_code)
    
    # Find the research.run call
    bug_found = False
    bug_details = []
    
    class ResearchCallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_orchestrator_run = False
            self.current_function = None
            
        def visit_FunctionDef(self, node):
            old_function = self.current_function
            old_in_run = self.in_orchestrator_run
            
            self.current_function = node.name
            if node.name == "run":
                self.in_orchestrator_run = True
            
            self.generic_visit(node)
            
            self.current_function = old_function
            self.in_orchestrator_run = old_in_run
        
        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)
        
        def visit_Await(self, node):
            nonlocal bug_found, bug_details
            
            if self.in_orchestrator_run and isinstance(node.value, ast.Call):
                call = node.value
                
                # Check if this is a research.run call
                if (isinstance(call.func, ast.Attribute) and 
                    call.func.attr == "run" and
                    isinstance(call.func.value, ast.Name) and
                    call.func.value.id == "research"):
                    
                    # Check the arguments
                    for keyword in call.keywords:
                        if keyword.arg is None:  # **kwargs
                            # Check if it's a dict merge with "db"
                            if isinstance(keyword.value, ast.Dict):
                                for key in keyword.value.keys:
                                    if isinstance(key, ast.Constant) and key.value == "db":
                                        bug_found = True
                                        bug_details.append({
                                            "line": node.lineno,
                                            "type": "dict_literal_with_db",
                                            "pattern": "research.run with 'db' in dict"
                                        })
                    
                    # Check positional arguments for dict merges
                    for arg in call.args[1:]:  # Skip job_id (first arg)
                        if isinstance(arg, ast.Dict):
                            # Check for {**base_payload, "db": db} pattern
                            for i, key in enumerate(arg.keys):
                                if key is None:  # **unpacking
                                    continue
                                if isinstance(key, ast.Constant) and key.value == "db":
                                    bug_found = True
                                    bug_details.append({
                                        "line": node.lineno,
                                        "type": "dict_merge_with_db",
                                        "pattern": '{**base_payload, "db": db}',
                                        "location": f"orchestrator.py line {node.lineno}"
                                    })
            
            self.generic_visit(node)
    
    visitor = ResearchCallVisitor()
    visitor.visit(tree)
    
    # Generate counterexample if bug found
    if bug_found:
        counterexample = {
            "bug_condition": "Orchestrator Database Coupling Violation",
            "details": bug_details,
            "formal_spec": "isBugCondition1(orchestrator_call) = TRUE",
            "explanation": (
                "The orchestrator passes the database session directly to research.run(), "
                "violating the blackboard pattern architecture. "
                "Agents should access the database through the blackboard pattern using job_id, "
                "not receive database sessions directly."
            ),
            "expected_fix": "research_result = await research.run(job_id, base_payload)",
            "current_code": "research_result = await research.run(job_id, {**base_payload, 'db': db})"
        }
        
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG DETECTED: Orchestrator Database Coupling Violation\n"
            f"{'='*80}\n\n"
            f"Counterexample:\n"
            f"  Location: {bug_details[0]['location']}\n"
            f"  Pattern: {bug_details[0]['pattern']}\n"
            f"  Type: {bug_details[0]['type']}\n\n"
            f"Formal Specification:\n"
            f"  isBugCondition1(orchestrator_call) = TRUE\n"
            f"  WHERE:\n"
            f"    - orchestrator_call.function_name == 'research.run'\n"
            f"    - 'db' IN orchestrator_call.arguments\n"
            f"    - orchestrator_call.arguments['db'] IS DatabaseSession\n\n"
            f"Violation:\n"
            f"  {counterexample['explanation']}\n\n"
            f"Current Code (INCORRECT):\n"
            f"  {counterexample['current_code']}\n\n"
            f"Expected Code (CORRECT):\n"
            f"  {counterexample['expected_fix']}\n\n"
            f"This test MUST FAIL on unfixed code to confirm the bug exists.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug is fixed
    assert not bug_found, (
        "Bug should be fixed: research.run should NOT receive 'db' in payload. "
        "Agents should access database through blackboard pattern using job_id."
    )


def test_bug_condition_line_237_verification():
    """
    Direct verification of line 237 in orchestrator.py
    
    This test specifically checks line 237 where the bug is documented to exist.
    """
    
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check line 237 (0-indexed, so line 236)
    if len(lines) >= 237:
        line_237 = lines[236].strip()
        
        # Check if line 237 contains the bug pattern
        has_research_call = "research.run" in line_237 or "research" in line_237
        has_db_param = '"db"' in line_237 or "'db'" in line_237 or ", db}" in line_237
        
        if has_research_call and has_db_param:
            pytest.fail(
                f"\n{'='*80}\n"
                f"BUG CONFIRMED AT LINE 237\n"
                f"{'='*80}\n\n"
                f"Line 237 content:\n"
                f"  {line_237}\n\n"
                f"This line passes the database session to research.run(), "
                f"violating the blackboard pattern.\n\n"
                f"Expected fix:\n"
                f"  research_result = await research.run(job_id, base_payload)\n\n"
                f"{'='*80}\n"
            )
    
    # If we reach here, line 237 doesn't have the bug pattern
    assert True, "Line 237 appears to be fixed or the bug is elsewhere"


def test_bug_condition_formal_specification_check():
    """
    Formal specification verification using pattern matching
    
    FUNCTION isBugCondition1(orchestrator_call)
      INPUT: orchestrator_call of type FunctionCall
      OUTPUT: boolean
      
      RETURN orchestrator_call.function_name == "research.run"
             AND "db" IN orchestrator_call.arguments
             AND orchestrator_call.arguments["db"] IS DatabaseSession
    END FUNCTION
    """
    
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Pattern matching for the bug
    # Look for: research.run(job_id, {**base_payload, "db": db})
    import re
    
    # Pattern 1: {**base_payload, "db": db}
    pattern1 = r'research\.run\([^,]+,\s*\{[^}]*"db"\s*:\s*db[^}]*\}'
    
    # Pattern 2: {**base_payload, 'db': db}
    pattern2 = r"research\.run\([^,]+,\s*\{[^}]*'db'\s*:\s*db[^}]*\}"
    
    matches = []
    for pattern in [pattern1, pattern2]:
        for match in re.finditer(pattern, source_code):
            line_num = source_code[:match.start()].count('\n') + 1
            matches.append({
                "line": line_num,
                "match": match.group(),
                "pattern": pattern
            })
    
    if matches:
        counterexample = matches[0]
        pytest.fail(
            f"\n{'='*80}\n"
            f"FORMAL SPECIFICATION VIOLATION DETECTED\n"
            f"{'='*80}\n\n"
            f"isBugCondition1(orchestrator_call) = TRUE\n\n"
            f"Counterexample:\n"
            f"  Line: {counterexample['line']}\n"
            f"  Code: {counterexample['match']}\n\n"
            f"Formal Specification Check:\n"
            f"  ✓ orchestrator_call.function_name == 'research.run'\n"
            f"  ✓ 'db' IN orchestrator_call.arguments\n"
            f"  ✓ orchestrator_call.arguments['db'] IS DatabaseSession\n\n"
            f"Result: Bug condition is TRUE - bug exists in the code.\n\n"
            f"This confirms the orchestrator violates the blackboard pattern by\n"
            f"passing the database session directly to the research agent.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug is fixed
    assert len(matches) == 0, "Bug should be fixed: no 'db' parameter in research.run calls"
