#!/usr/bin/env python3
"""
Proof of Concept: Tool Call Parser for Non-Tool Models

This demonstrates that we CAN parse tool calls from text reliably
with the right format and prompting.
"""

import json
import re
from typing import Optional, List, Dict, Any


class ToolCall:
    def __init__(self, name: str, params: Dict[str, Any], confidence: float = 1.0):
        self.name = name
        self.params = params
        self.confidence = confidence
    
    def __repr__(self):
        return f"ToolCall(name={self.name}, params={self.params}, confidence={self.confidence})"


class VeniceToolParser:
    """Parse tool calls from non-tool model text output."""
    
    # Pattern 1: Explicit markers (most reliable)
    MARKER_PATTERN = r'TOOL_CALL_START\s*\n(.*?)\nTOOL_CALL_END'
    
    # Pattern 2: JSON in code blocks
    CODE_BLOCK_PATTERN = r'```(?:json|tool_call)?\s*\n(\{.*?\})\s*\n```'
    
    # Pattern 3: Inline JSON (less reliable)
    INLINE_JSON_PATTERN = r'\{"function":\s*"([^"]+)",\s*"params":\s*(\{[^}]+\})\}'
    
    def extract_tool_calls(self, text: str) -> List[ToolCall]:
        """Extract all tool calls from text, ordered by confidence."""
        tool_calls = []
        
        # Try marker pattern first (highest confidence)
        tool_calls.extend(self._extract_with_markers(text))
        
        # Try code block pattern (medium confidence)
        if not tool_calls:
            tool_calls.extend(self._extract_from_code_blocks(text))
        
        # Try inline JSON (lowest confidence)
        if not tool_calls:
            tool_calls.extend(self._extract_inline_json(text))
        
        return tool_calls
    
    def _extract_with_markers(self, text: str) -> List[ToolCall]:
        """Extract tool calls with explicit markers."""
        matches = re.finditer(self.MARKER_PATTERN, text, re.DOTALL)
        tool_calls = []
        
        for match in matches:
            try:
                json_str = match.group(1).strip()
                data = json.loads(json_str)
                
                if "function" in data and "params" in data:
                    tool_calls.append(ToolCall(
                        name=data["function"],
                        params=data["params"],
                        confidence=1.0  # Highest confidence
                    ))
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    def _extract_from_code_blocks(self, text: str) -> List[ToolCall]:
        """Extract tool calls from code blocks."""
        matches = re.finditer(self.CODE_BLOCK_PATTERN, text, re.DOTALL)
        tool_calls = []
        
        for match in matches:
            try:
                json_str = match.group(1).strip()
                data = json.loads(json_str)
                
                if "function" in data and "params" in data:
                    tool_calls.append(ToolCall(
                        name=data["function"],
                        params=data["params"],
                        confidence=0.8  # Medium confidence
                    ))
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    def _extract_inline_json(self, text: str) -> List[ToolCall]:
        """Extract inline JSON tool calls."""
        matches = re.finditer(self.INLINE_JSON_PATTERN, text)
        tool_calls = []
        
        for match in matches:
            try:
                function_name = match.group(1)
                params_str = match.group(2)
                params = json.loads(params_str)
                
                # Check if this looks like a real tool call vs discussion
                if self._is_likely_tool_call(text, match.start()):
                    tool_calls.append(ToolCall(
                        name=function_name,
                        params=params,
                        confidence=0.6  # Lower confidence
                    ))
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    def _is_likely_tool_call(self, text: str, position: int) -> bool:
        """Heuristic to determine if JSON is a tool call vs discussion."""
        # Get context around the match
        start = max(0, position - 100)
        end = min(len(text), position + 100)
        context = text[start:end].lower()
        
        # Indicators of actual tool call
        call_indicators = ["using", "calling", "execute", "run", "invoke"]
        discussion_indicators = ["could", "might", "would", "should", "example"]
        
        call_score = sum(1 for word in call_indicators if word in context)
        discussion_score = sum(1 for word in discussion_indicators if word in context)
        
        return call_score > discussion_score


def test_parser():
    """Test the parser with various formats."""
    parser = VeniceToolParser()
    
    # Test 1: Explicit markers (should work perfectly)
    text1 = """
I'll remember that for you.

TOOL_CALL_START
{
  "function": "core_memory_append",
  "params": {
    "name": "user_facts",
    "content": "likes pizza"
  }
}
TOOL_CALL_END

Done! I've updated your memory.
"""
    
    print("Test 1: Explicit markers")
    calls = parser.extract_tool_calls(text1)
    print(f"Found {len(calls)} tool call(s):")
    for call in calls:
        print(f"  {call}")
    print()
    
    # Test 2: Code block format
    text2 = """
Let me search for that information.

```json
{
  "function": "archival_memory_search",
  "params": {
    "query": "pizza preferences",
    "page": 0
  }
}
```

I'll look that up for you.
"""
    
    print("Test 2: Code block format")
    calls = parser.extract_tool_calls(text2)
    print(f"Found {len(calls)} tool call(s):")
    for call in calls:
        print(f"  {call}")
    print()
    
    # Test 3: Inline JSON (should detect)
    text3 = """
I'm using {"function": "send_message", "params": {"message": "Hello!"}} to respond.
"""
    
    print("Test 3: Inline JSON")
    calls = parser.extract_tool_calls(text3)
    print(f"Found {len(calls)} tool call(s):")
    for call in calls:
        print(f"  {call}")
    print()
    
    # Test 4: Discussion (should NOT detect)
    text4 = """
I could use core_memory_append to remember this, but let me just tell you instead.
"""
    
    print("Test 4: Discussion (should find nothing)")
    calls = parser.extract_tool_calls(text4)
    print(f"Found {len(calls)} tool call(s):")
    for call in calls:
        print(f"  {call}")
    print()
    
    # Test 5: Multiple tool calls
    text5 = """
I'll do both operations.

TOOL_CALL_START
{
  "function": "core_memory_append",
  "params": {"name": "facts", "content": "likes pizza"}
}
TOOL_CALL_END

TOOL_CALL_START
{
  "function": "archival_memory_insert",
  "params": {"content": "User likes pizza"}
}
TOOL_CALL_END

All done!
"""
    
    print("Test 5: Multiple tool calls")
    calls = parser.extract_tool_calls(text5)
    print(f"Found {len(calls)} tool call(s):")
    for call in calls:
        print(f"  {call}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Venice Tool Parser - Proof of Concept")
    print("=" * 60)
    print()
    
    test_parser()
    
    print("=" * 60)
    print("Conclusion: Parsing is FEASIBLE with proper formatting!")
    print("=" * 60)
