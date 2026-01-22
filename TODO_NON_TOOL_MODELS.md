# TODO: Enable Non-Tool Models as Letta Agents

## Goal
Make Venice models without native tool support (like `venice-uncensored`) work as functional Letta agents through intelligent parsing and multi-turn conversation.

## Current Status
- ✅ Non-tool models work for simple chat
- ❌ Can't be used as agents (memory/tools don't work)
- ❌ Output tool calls as text instead of executing them

## The Challenge

### What We Need to Solve:
1. **Parse tool calls from text** - Detect when model wants to call a tool
2. **Execute tools** - Actually run the tool and get results
3. **Feed results back** - Get tool results back to the model
4. **Handle errors** - Let model retry if tool fails
5. **Maintain conversation flow** - Keep context coherent

### Why It's Hard:
- No structured tool call format
- Model generates full response before we can intervene
- Can't inject tool results mid-generation
- Ambiguity between discussing tools vs calling them

## Proposed Solution: Multi-Turn Tool Execution Loop

### Architecture Overview

```
User Message
    ↓
Model Response (with tool call in text)
    ↓
[PARSER] Detect tool call
    ↓
[EXECUTOR] Run tool, get result
    ↓
[INJECTOR] Send result back as system message
    ↓
Model Response (continues with tool result)
    ↓
User sees final response
```

### Implementation Plan

#### Phase 1: Tool Call Detection
**File:** `letta/llm_api/venice_tool_parser.py` (new)

```python
class VeniceToolParser:
    """Parse tool calls from non-tool model text output."""
    
    TOOL_PATTERNS = [
        # JSON format: {"function": "name", "params": {...}}
        r'\{"function":\s*"([^"]+)",\s*"params":\s*(\{[^}]+\})\}',
        
        # XML-like format: <tool_call name="..." params="..." />
        r'<tool_call\s+name="([^"]+)"\s+params="([^"]+)"\s*/>',
        
        # Markdown format: ```tool_call\n{json}\n```
        r'```tool_call\s*\n(\{[^`]+\})\n```',
    ]
    
    def detect_tool_call(self, text: str) -> Optional[ToolCall]:
        """
        Detect if text contains a tool call.
        
        Returns:
            ToolCall object if found, None otherwise
        """
        pass
    
    def extract_tool_calls(self, text: str) -> List[ToolCall]:
        """Extract all tool calls from text."""
        pass
    
    def is_discussing_tool(self, text: str, tool_name: str) -> bool:
        """
        Determine if model is discussing a tool vs calling it.
        
        Heuristics:
        - "I could use X" = discussing
        - "Using X with params Y" = calling
        - JSON format = definitely calling
        """
        pass
```

**Tasks:**
- [ ] Implement multiple parsing strategies (JSON, XML, markdown)
- [ ] Add confidence scoring for detected tool calls
- [ ] Handle malformed JSON gracefully
- [ ] Distinguish between discussion and actual calls
- [ ] Support multiple tool calls in one response

#### Phase 2: Prompt Engineering
**File:** `letta/prompts/non_tool_agent_prompt.py` (new)

```python
NON_TOOL_AGENT_SYSTEM_PROMPT = """
You are a Letta agent with access to tools. When you want to use a tool, 
output it in this EXACT format:

TOOL_CALL_START
{
  "function": "tool_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
TOOL_CALL_END

After outputting a tool call, STOP generating. Wait for the tool result.

Available tools:
{tools_list}

Example:
User: Remember that I like pizza
Assistant: I'll remember that for you.
TOOL_CALL_START
{
  "function": "core_memory_append",
  "params": {
    "name": "user_preferences", 
    "content": "likes pizza"
  }
}
TOOL_CALL_END
"""
```

**Tasks:**
- [ ] Design clear tool call format
- [ ] Add examples for each tool type
- [ ] Include error handling instructions
- [ ] Test with various non-tool models
- [ ] Optimize for minimal token usage

#### Phase 3: Multi-Turn Execution Loop
**File:** `letta/agents/non_tool_agent_loop.py` (new)

```python
class NonToolAgentLoop:
    """
    Agent loop for models without native tool support.
    Uses multi-turn conversation to execute tools.
    """
    
    async def step_with_tool_parsing(
        self,
        input_messages: List[MessageCreate],
        max_tool_iterations: int = 5
    ) -> LettaResponse:
        """
        Execute agent step with tool call parsing.
        
        Flow:
        1. Send messages to model
        2. Parse response for tool calls
        3. If tool call found:
           a. Execute tool
           b. Inject result as system message
           c. Get model's continuation (goto 2)
        4. Return final response
        """
        
        messages = input_messages.copy()
        tool_iterations = 0
        
        while tool_iterations < max_tool_iterations:
            # Get model response
            response = await self._generate_response(messages)
            
            # Check for tool calls
            tool_calls = self.parser.extract_tool_calls(response.content)
            
            if not tool_calls:
                # No tools, we're done
                return response
            
            # Execute tools
            for tool_call in tool_calls:
                result = await self._execute_tool(tool_call)
                
                # Inject result back into conversation
                messages.append({
                    "role": "system",
                    "content": f"Tool '{tool_call.name}' result: {result}"
                })
            
            # Continue conversation with tool results
            tool_iterations += 1
        
        # Max iterations reached
        return response
```

**Tasks:**
- [ ] Implement multi-turn loop
- [ ] Add tool execution with error handling
- [ ] Inject results as system messages
- [ ] Handle max iteration limits
- [ ] Preserve conversation context
- [ ] Support streaming (challenging!)

#### Phase 4: Venice Client Integration
**File:** `letta/llm_api/venice_client.py` (modify)

```python
class VeniceClient(OpenAIClient):
    def __init__(self):
        super().__init__()
        self.tool_parser = VeniceToolParser()
        self.use_tool_parsing = True  # Enable for non-tool models
    
    async def request_async_with_tool_parsing(
        self, 
        request_data: dict, 
        llm_config: LLMConfig
    ) -> dict:
        """
        Enhanced request that handles tool parsing for non-tool models.
        """
        model = request_data.get("model", "")
        
        if not self._supports_tools(model) and self.use_tool_parsing:
            # Use multi-turn tool execution
            return await self._request_with_parsed_tools(request_data, llm_config)
        else:
            # Normal request for tool-supporting models
            return await super().request_async(request_data, llm_config)
```

**Tasks:**
- [ ] Add tool parsing mode toggle
- [ ] Integrate with NonToolAgentLoop
- [ ] Modify system prompts for non-tool models
- [ ] Handle streaming responses
- [ ] Add telemetry/logging

#### Phase 5: Testing & Validation
**File:** `tests/test_non_tool_agent.py` (new)

```python
@pytest.mark.asyncio
async def test_venice_uncensored_memory():
    """Test that venice-uncensored can update memory."""
    agent = create_agent(model="venice-uncensored")
    
    response = await agent.send_message("Remember that I like pizza")
    
    # Check that memory was actually updated
    memory = await agent.get_memory()
    assert "pizza" in memory.core_memory
```

**Test Cases:**
- [ ] Memory append/replace operations
- [ ] Archival search and insert
- [ ] Multiple tool calls in sequence
- [ ] Error handling and retries
- [ ] Conversation continuity
- [ ] Streaming responses
- [ ] Edge cases (malformed JSON, etc.)

## Challenges to Solve

### 1. Streaming Support
**Problem:** Tool parsing requires complete response, but streaming sends chunks.

**Potential Solutions:**
- Buffer chunks until tool call detected
- Use special markers to detect tool calls early
- Fall back to non-streaming for non-tool models

### 2. Ambiguity Detection
**Problem:** Model might discuss tools without calling them.

**Potential Solutions:**
- Require explicit format (TOOL_CALL_START/END)
- Use confidence scoring
- Add confirmation step ("Execute this tool? Y/N")

### 3. Context Window Management
**Problem:** Multi-turn loop adds messages, consuming context.

**Potential Solutions:**
- Compress tool results
- Remove intermediate tool messages after execution
- Use summary messages instead of full tool results

### 4. Error Recovery
**Problem:** Tool execution might fail, model needs to retry.

**Potential Solutions:**
- Include error details in result message
- Provide suggestions for fixes
- Allow model to try alternative approaches

### 5. Performance
**Problem:** Multi-turn loop is slower than native tool calls.

**Potential Solutions:**
- Cache parsed tool calls
- Optimize prompt engineering
- Parallel tool execution where possible

## Success Metrics

### Must Have:
- [ ] Memory operations work reliably (95%+ success rate)
- [ ] Archival search returns correct results
- [ ] Conversation flow feels natural
- [ ] No worse than 2x latency vs tool-supporting models

### Nice to Have:
- [ ] Streaming support
- [ ] Sub-second tool execution
- [ ] Automatic error recovery
- [ ] Support for custom tools

## Alternative Approaches

### Approach A: Fine-tune a Wrapper Model
Train a small model to translate between formats:
```
Non-tool model output → Wrapper → Structured tool calls
```

**Pros:** More reliable parsing
**Cons:** Requires training, maintenance

### Approach B: Use Function Calling Prompt
Heavily engineer prompts to force JSON output:
```
"You MUST output tool calls as valid JSON. Example: {...}"
```

**Pros:** Simpler implementation
**Cons:** Model might not follow instructions

### Approach C: Hybrid Mode
Use tool-supporting model for tool decisions, non-tool model for responses:
```
Tool model: "Should call core_memory_append"
Non-tool model: "Here's my response..."
```

**Pros:** Best of both worlds
**Cons:** Complex, requires two models

## Timeline Estimate

- **Phase 1 (Parsing):** 2-3 days
- **Phase 2 (Prompts):** 1-2 days
- **Phase 3 (Loop):** 3-5 days
- **Phase 4 (Integration):** 2-3 days
- **Phase 5 (Testing):** 3-5 days

**Total:** ~2-3 weeks for MVP

## Next Steps

1. **Prototype the parser** - Start with simple JSON detection
2. **Test with venice-uncensored** - See if it can follow format
3. **Build minimal loop** - Single tool call, no streaming
4. **Iterate based on results** - Refine approach

## Notes

- This is experimental - might not work perfectly
- Some models may follow instructions better than others
- Could be valuable for the community even if imperfect
- Consider contributing back to Letta if successful

## Questions to Answer

1. Can we get non-tool models to consistently output structured tool calls?
2. How much latency is acceptable for multi-turn loop?
3. Should we support streaming or only blocking mode?
4. What's the minimum viable feature set?
5. How do we handle models that refuse to follow format?

---

**Status:** Planning phase - ready to prototype
**Priority:** Medium (nice-to-have, not critical)
**Difficulty:** High (requires careful design and testing)
