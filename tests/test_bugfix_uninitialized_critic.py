"""
Bug Condition Exploration Test - Uninitialized critic_result Variable

**Validates: Requirements 1.3, 1.4**

This test explores the bug condition where critic_result is initialized as an empty dict {},
which causes incorrect final report assembly when the critic agent fails or is skipped,
resulting in missing verdict and score data.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected Outcome: Test FAILS with counterexample showing None/missing values for critic fields.
"""

import pytest
import ast
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_bug_condition_uninitialized_critic_result_static_analysis():
    """
    Property 1: Bug Condition - Uninitialized Variable Bug (Static Analysis)
    
    **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists.
    
    Bug Condition: critic_result initialized as empty dict {} instead of proper defaults
    
    This test uses static code analysis to detect the bug pattern without
    needing to execute the code or deal with import dependencies.
    
    Expected on UNFIXED code: Test FAILS - finds critic_result = {}
    Expected on FIXED code: Test PASSES - critic_result has proper default structure
    """
    
    # Read the orchestrator.py file
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    assert orchestrator_path.exists(), f"Orchestrator file not found at {orchestrator_path}"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Parse the AST
    tree = ast.parse(source_code)
    
    # Find the critic_result initialization
    bug_found = False
    bug_details = []
    
    class CriticInitVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_run_function = False
            
        def visit_FunctionDef(self, node):
            old_in_run = self.in_run_function
            if node.name == "run":
                self.in_run_function = True
            
            self.generic_visit(node)
            self.in_run_function = old_in_run
        
        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)
        
        def visit_Assign(self, node):
            nonlocal bug_found, bug_details
            
            if self.in_run_function:
                # Check if this is critic_result assignment
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "critic_result":
                        # Check if the value is an empty dict {}
                        if isinstance(node.value, ast.Dict):
                            if len(node.value.keys) == 0 and len(node.value.values) == 0:
                                bug_found = True
                                bug_details.append({
                                    "line": node.lineno,
                                    "type": "empty_dict_initialization",
                                    "pattern": "critic_result = {}",
                                    "location": f"orchestrator.py line {node.lineno}"
                                })
            
            self.generic_visit(node)
    
    visitor = CriticInitVisitor()
    visitor.visit(tree)
    
    # Generate counterexample if bug found
    if bug_found:
        counterexample = {
            "bug_condition": "Uninitialized Variable Bug",
            "details": bug_details,
            "formal_spec": "isBugCondition2(execution_state) = TRUE",
            "explanation": (
                "The critic_result variable is initialized as an empty dict {}, "
                "which causes incorrect final report assembly when the critic agent fails or is skipped. "
                "When critic_result.get('score') is called on an empty dict, it returns None, "
                "resulting in final reports with critic_score=None and missing verdict data."
            ),
            "expected_fix": (
                'critic_result = {\n'
                '    "verdict": "SKIPPED",\n'
                '    "score": 0,\n'
                '    "issues": ["Critic agent was not executed"],\n'
                '    "improvement_prompt": ""\n'
                '}'
            ),
            "current_code": "critic_result = {}"
        }
        
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG DETECTED: Uninitialized Variable Bug\n"
            f"{'='*80}\n\n"
            f"Counterexample:\n"
            f"  Location: {bug_details[0]['location']}\n"
            f"  Pattern: {bug_details[0]['pattern']}\n"
            f"  Type: {bug_details[0]['type']}\n\n"
            f"Formal Specification:\n"
            f"  isBugCondition2(execution_state) = TRUE\n"
            f"  WHERE:\n"
            f"    - execution_state.critic_result == {{}}\n"
            f"    - execution_state.critic_failed OR execution_state.critic_skipped\n"
            f"    - execution_state.assembling_final_report == True\n\n"
            f"Violation:\n"
            f"  {counterexample['explanation']}\n\n"
            f"Current Code (INCORRECT):\n"
            f"  {counterexample['current_code']}\n\n"
            f"Expected Code (CORRECT):\n"
            f"  {counterexample['expected_fix']}\n\n"
            f"Impact:\n"
            f"  When critic agent fails or is skipped:\n"
            f"    - Final report has critic_score: None (should be 0)\n"
            f"    - Final report has critic_verdict: 'APPROVED' (should be 'SKIPPED')\n"
            f"    - No indication that critic was not executed\n\n"
            f"This test MUST FAIL on unfixed code to confirm the bug exists.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug is fixed
    assert not bug_found, (
        "Bug should be fixed: critic_result should be initialized with proper default structure, "
        "not an empty dict."
    )


def test_bug_condition_critic_result_final_report_impact():
    """
    Verify the impact of empty critic_result on final report assembly
    
    This test checks that when critic_result is {}, the final report
    will have None/missing values for critic fields.
    """
    
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Check for the problematic pattern in final report assembly
    # Look for: critic_result.get("score") and critic_result.get("verdict")
    import re
    
    # Find critic_result initialization
    init_pattern = r'critic_result\s*=\s*\{\}'
    init_matches = list(re.finditer(init_pattern, source_code))
    
    # Find final report usage
    score_pattern = r'critic_result\.get\(["\']score["\']\)'
    verdict_pattern = r'critic_result\.get\(["\']verdict["\'](,\s*["\'][^"\']+["\']\))?'
    
    score_matches = list(re.finditer(score_pattern, source_code))
    verdict_matches = list(re.finditer(verdict_pattern, source_code))
    
    if init_matches and (score_matches or verdict_matches):
        init_line = source_code[:init_matches[0].start()].count('\n') + 1
        
        usage_details = []
        for match in score_matches:
            line_num = source_code[:match.start()].count('\n') + 1
            usage_details.append(f"Line {line_num}: {match.group()}")
        
        for match in verdict_matches:
            line_num = source_code[:match.start()].count('\n') + 1
            usage_details.append(f"Line {line_num}: {match.group()}")
        
        pytest.fail(
            f"\n{'='*80}\n"
            f"BUG IMPACT CONFIRMED: Empty critic_result Causes Incorrect Final Reports\n"
            f"{'='*80}\n\n"
            f"Bug Pattern Detected:\n"
            f"  1. critic_result initialized as empty dict at line {init_line}\n"
            f"  2. Final report uses critic_result.get() which returns None for missing keys\n\n"
            f"Usage in Final Report:\n"
            f"  " + "\n  ".join(usage_details) + "\n\n"
            f"Impact:\n"
            f"  When critic agent fails or is skipped:\n"
            f"    - critic_result = {{}}\n"
            f"    - critic_result.get('score') returns None\n"
            f"    - critic_result.get('verdict', 'APPROVED') returns 'APPROVED'\n"
            f"    - Final report shows: critic_score=None, critic_verdict='APPROVED'\n"
            f"    - Users cannot tell if critic ran or not\n\n"
            f"Expected Behavior:\n"
            f"  When critic agent fails or is skipped:\n"
            f"    - critic_result should have default values\n"
            f"    - critic_score should be 0 (not None)\n"
            f"    - critic_verdict should be 'SKIPPED' (not 'APPROVED')\n"
            f"    - issues should indicate 'Critic agent was not executed'\n\n"
            f"This confirms the bug exists and impacts final report quality.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug pattern is not found
    assert True, "Bug pattern not found or already fixed"


def test_bug_condition_line_117_verification():
    """
    Direct verification of line 117 in orchestrator.py where critic_result is initialized
    
    This test specifically checks line 117 where the bug is documented to exist.
    """
    
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check line 117 (0-indexed, so line 116)
    if len(lines) >= 117:
        line_117 = lines[116].strip()
        
        # Check if line 117 contains the bug pattern
        has_critic_result = "critic_result" in line_117
        has_empty_dict = "= {}" in line_117
        
        if has_critic_result and has_empty_dict:
            pytest.fail(
                f"\n{'='*80}\n"
                f"BUG CONFIRMED AT LINE 117\n"
                f"{'='*80}\n\n"
                f"Line 117 content:\n"
                f"  {line_117}\n\n"
                f"This line initializes critic_result as an empty dict, which causes\n"
                f"incorrect final report assembly when the critic agent fails or is skipped.\n\n"
                f"Expected fix:\n"
                f"  critic_result = {{\n"
                f"      'verdict': 'SKIPPED',\n"
                f"      'score': 0,\n"
                f"      'issues': ['Critic agent was not executed'],\n"
                f"      'improvement_prompt': ''\n"
                f"  }}\n\n"
                f"Impact:\n"
                f"  - Final report will have critic_score=None instead of 0\n"
                f"  - Final report will have critic_verdict='APPROVED' instead of 'SKIPPED'\n"
                f"  - No indication that critic was not executed\n\n"
                f"{'='*80}\n"
            )
    
    # If we reach here, line 117 doesn't have the bug pattern
    assert True, "Line 117 appears to be fixed or the bug is elsewhere"


def test_bug_condition_formal_specification_check():
    """
    Formal specification verification using pattern matching
    
    FUNCTION isBugCondition2(execution_state)
      INPUT: execution_state of type OrchestrationState
      OUTPUT: boolean
      
      RETURN execution_state.critic_result == {}
             AND (execution_state.critic_failed OR execution_state.critic_skipped)
             AND execution_state.assembling_final_report == True
    END FUNCTION
    """
    
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Pattern matching for the bug
    # Look for: critic_result = {}
    import re
    
    # Pattern: critic_result = {}
    pattern = r'critic_result\s*=\s*\{\}\s*(?:#.*)?'
    
    matches = []
    for match in re.finditer(pattern, source_code):
        line_num = source_code[:match.start()].count('\n') + 1
        
        # Get the full line for context
        lines = source_code.split('\n')
        full_line = lines[line_num - 1] if line_num <= len(lines) else ""
        
        matches.append({
            "line": line_num,
            "match": match.group().strip(),
            "full_line": full_line.strip(),
            "pattern": pattern
        })
    
    if matches:
        counterexample = matches[0]
        
        # Check if this is in the run function and used in final report
        # This confirms all three conditions of the formal spec
        in_run_function = "async def run" in source_code or "def run" in source_code
        has_final_report_usage = "critic_result.get" in source_code
        
        if in_run_function and has_final_report_usage:
            pytest.fail(
                f"\n{'='*80}\n"
                f"FORMAL SPECIFICATION VIOLATION DETECTED\n"
                f"{'='*80}\n\n"
                f"isBugCondition2(execution_state) = TRUE\n\n"
                f"Counterexample:\n"
                f"  Line: {counterexample['line']}\n"
                f"  Code: {counterexample['full_line']}\n\n"
                f"Formal Specification Check:\n"
                f"  ✓ execution_state.critic_result == {{}}\n"
                f"  ✓ execution_state.critic_failed OR execution_state.critic_skipped\n"
                f"     (when critic agent fails, critic_result remains {{}})\n"
                f"  ✓ execution_state.assembling_final_report == True\n"
                f"     (final report uses critic_result.get() on empty dict)\n\n"
                f"Result: Bug condition is TRUE - bug exists in the code.\n\n"
                f"This confirms that when the critic agent fails or is skipped,\n"
                f"the empty dict initialization causes incorrect final reports with:\n"
                f"  - critic_score: None (should be 0)\n"
                f"  - critic_verdict: 'APPROVED' (should be 'SKIPPED')\n"
                f"  - No indication that critic was not executed\n\n"
                f"Expected Behavior:\n"
                f"  critic_result should be initialized with proper defaults:\n"
                f"  {{\n"
                f"      'verdict': 'SKIPPED',\n"
                f"      'score': 0,\n"
                f"      'issues': ['Critic agent was not executed'],\n"
                f"      'improvement_prompt': ''\n"
                f"  }}\n"
                f"{'='*80}\n"
            )
    
    # If we reach here, the bug is fixed
    assert len(matches) == 0, "Bug should be fixed: critic_result should have proper default structure"


def test_bug_condition_semantic_verification():
    """
    Semantic verification: Check that empty dict causes None values in final report
    
    This test verifies the semantic impact of the bug by checking that:
    1. critic_result is initialized as {}
    2. Final report uses .get() which returns None for missing keys
    3. This results in incorrect final report data
    """
    
    orchestrator_path = Path(__file__).parent.parent / "app" / "agents" / "orchestrator.py"
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Parse the AST to find the semantic bug
    tree = ast.parse(source_code)
    
    # Track initialization and usage
    has_empty_init = False
    init_line = None
    usage_lines = []
    
    class SemanticBugVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_run_function = False
            
        def visit_FunctionDef(self, node):
            old_in_run = self.in_run_function
            if node.name == "run":
                self.in_run_function = True
            
            self.generic_visit(node)
            self.in_run_function = old_in_run
        
        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)
        
        def visit_Assign(self, node):
            nonlocal has_empty_init, init_line
            
            if self.in_run_function:
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "critic_result":
                        if isinstance(node.value, ast.Dict) and len(node.value.keys) == 0:
                            has_empty_init = True
                            init_line = node.lineno
            
            self.generic_visit(node)
        
        def visit_Call(self, node):
            nonlocal usage_lines
            
            if self.in_run_function:
                # Check for critic_result.get() calls
                if isinstance(node.func, ast.Attribute):
                    if (node.func.attr == "get" and 
                        isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == "critic_result"):
                        usage_lines.append(node.lineno)
            
            self.generic_visit(node)
    
    visitor = SemanticBugVisitor()
    visitor.visit(tree)
    
    if has_empty_init and usage_lines:
        pytest.fail(
            f"\n{'='*80}\n"
            f"SEMANTIC BUG VERIFIED: Empty Dict Causes None Values\n"
            f"{'='*80}\n\n"
            f"Bug Pattern:\n"
            f"  1. critic_result initialized as {{}} at line {init_line}\n"
            f"  2. critic_result.get() called at lines: {', '.join(map(str, usage_lines))}\n"
            f"  3. When critic fails/skips, .get() returns None for missing keys\n\n"
            f"Semantic Impact:\n"
            f"  critic_result = {{}}  # Empty dict\n"
            f"  critic_result.get('score')  # Returns None (not 0)\n"
            f"  critic_result.get('verdict', 'APPROVED')  # Returns 'APPROVED' (not 'SKIPPED')\n\n"
            f"This causes final reports to have:\n"
            f"  - critic_score: None (incorrect, should be 0)\n"
            f"  - critic_verdict: 'APPROVED' (misleading, should be 'SKIPPED')\n\n"
            f"Expected Behavior:\n"
            f"  Initialize with proper defaults so .get() returns meaningful values:\n"
            f"  critic_result = {{\n"
            f"      'verdict': 'SKIPPED',\n"
            f"      'score': 0,\n"
            f"      'issues': ['Critic agent was not executed'],\n"
            f"      'improvement_prompt': ''\n"
            f"  }}\n\n"
            f"This semantic analysis confirms the bug exists and impacts data quality.\n"
            f"{'='*80}\n"
        )
    
    # If we reach here, the bug is fixed
    assert not (has_empty_init and usage_lines), "Bug should be fixed"
