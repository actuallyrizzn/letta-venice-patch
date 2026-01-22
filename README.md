# Letta Venice AI Patch

A monkeypatch to add Venice AI provider support to your existing Letta installation.

## What This Does

This patch adds Venice AI as a provider to Letta, enabling you to use Venice's privacy-focused AI models (including models with native chain-of-thought reasoning) within the Letta framework.

**Features:**
- ✅ Full streaming support (step and token streaming)
- ✅ Run tracking and cancellation
- ✅ Chain-of-thought reasoning extraction from `<think>` tags
- ✅ Tool calling support
- ✅ Compatible with Letta ADE (Agent Development Environment)

## Installation

### Prerequisites
- Letta v0.16.3 or compatible version
- Python 3.10+
- Venice AI API key (get one at https://venice.ai)

### Quick Install

```bash
# Clone this repo
git clone https://github.com/actuallyrizzn/letta-venice-patch.git
cd letta-venice-patch

# Run the patch script
python patch.py /path/to/your/letta/installation

# Or if you installed Letta via pip:
python patch.py $(python -c "import letta; print(letta.__path__[0])")
```

### Manual Installation

If you prefer to apply the patch manually:

```bash
# Copy the Venice provider files
cp patches/venice.py /path/to/letta/schemas/providers/
cp patches/venice_client.py /path/to/letta/llm_api/

# Apply the patches
python apply_patches.py /path/to/letta
```

## Configuration

### Set Your Venice API Key

**Option 1: Environment Variable**
```bash
export VENICE_API_KEY="your-venice-api-key-here"
```

**Option 2: Letta Config File**
Add to `~/.letta/.env`:
```
VENICE_API_KEY=your-venice-api-key-here
```

### Enable Run Tracking (Required for Streaming)

```bash
export LETTA_TRACK_AGENT_RUN="true"
```

Or add to your Letta startup script.

## Usage

### CLI
```bash
# Start Letta server
letta server

# Create an agent with Venice model
letta run --model venice/qwen3-4b
```

### Python API
```python
from letta import create_client

client = create_client()

# Create agent with Venice model
agent = client.create_agent(
    name="venice-agent",
    llm_config={
        "model": "qwen3-4b",
        "model_endpoint_type": "venice",
        "model_endpoint": "https://api.venice.ai/api/v1"
    }
)

# Send a message
response = client.send_message(
    agent_id=agent.id,
    message="Hello! Can you help me with something?",
    role="user"
)
```

### Available Venice Models

- `qwen3-4b` - Fast, efficient model with CoT reasoning
- `kimi-k2-thinking` - Advanced reasoning model
- `llama-3.3-70b` - Powerful general-purpose model
- `deepseek-r1` - Deep reasoning model
- And many more at https://venice.ai/models

## What Gets Patched

This patch modifies the following Letta components:

1. **Provider System**
   - Adds Venice to provider enums
   - Registers Venice provider with model endpoints

2. **LLM Client**
   - Adds `VeniceClient` that extends OpenAI client
   - Filters `None` values (Venice API is strict about nulls)
   - Extracts `<think>` tags as reasoning content

3. **Streaming Service**
   - Adds Venice to compatible streaming models list

4. **Settings**
   - Adds `venice_api_key` and `venice_base_url` configuration

## Uninstalling

```bash
python unpatch.py /path/to/letta
```

This will restore your Letta installation to its original state.

## Troubleshooting

### "run_id is required when enforce_run_id_set is True"
Make sure `LETTA_TRACK_AGENT_RUN="true"` is set in your environment.

### "max_completion_tokens: null" API Error
This is fixed by the patch - make sure you ran the patch script successfully.

### `<think>` Tags Showing in Output
This is fixed by the patch - the reasoning should be extracted and displayed separately in the ADE.

### Venice Models Not Showing in ADE
Restart your Letta server after applying the patch.

## Contributing

Found a bug or want to improve the patch? PRs welcome!

## Related

- **Official Issue:** https://github.com/letta-ai/letta/issues/3161
- **Full Integration Fork:** https://github.com/technonomicon-lore/letta
- **Venice AI:** https://venice.ai
- **Letta:** https://github.com/letta-ai/letta

## License

MIT License - See LICENSE file for details

## Disclaimer

This is an unofficial patch. Use at your own risk. For production use, we recommend waiting for official Venice support in Letta or using our maintained fork.
