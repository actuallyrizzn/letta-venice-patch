#!/usr/bin/env python3
"""
Letta Venice AI Patch Script

Applies Venice AI provider support to an existing Letta installation.
"""

import os
import sys
import shutil
import re
from pathlib import Path


def backup_file(file_path):
    """Create a backup of a file before modifying it."""
    backup_path = f"{file_path}.backup"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"  ✓ Backed up: {file_path}")
    return backup_path


def patch_enums(letta_path):
    """Add venice to ProviderType enum."""
    enums_path = os.path.join(letta_path, "schemas", "enums.py")
    
    if not os.path.exists(enums_path):
        print(f"  ✗ Not found: {enums_path}")
        return False
    
    backup_file(enums_path)
    
    with open(enums_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'venice = "venice"' in content:
        print(f"  ⊙ Already patched: {enums_path}")
        return True
    
    # Add venice to ProviderType
    pattern = r'(class ProviderType\(str, Enum\):.*?)((?:\n    \w+ = "[^"]+"\n)+)'
    
    def add_venice(match):
        class_def = match.group(1)
        entries = match.group(2)
        # Add venice before the last entry
        return class_def + entries.rstrip() + '\n    venice = "venice"\n'
    
    content = re.sub(pattern, add_venice, content, flags=re.DOTALL)
    
    with open(enums_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {enums_path}")
    return True


def patch_llm_config(letta_path):
    """Add venice to LLM config schemas."""
    llm_config_path = os.path.join(letta_path, "schemas", "llm_config.py")
    
    if not os.path.exists(llm_config_path):
        print(f"  ✗ Not found: {llm_config_path}")
        return False
    
    backup_file(llm_config_path)
    
    with open(llm_config_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if '"venice"' in content:
        print(f"  ⊙ Already patched: {llm_config_path}")
        return True
    
    # Add venice to Literal types
    content = re.sub(
        r'(Literal\[[^\]]*)"groq"([^\]]*\])',
        r'\1"groq", "venice"\2',
        content
    )
    
    with open(llm_config_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {llm_config_path}")
    return True


def patch_settings(letta_path):
    """Add Venice settings."""
    settings_path = os.path.join(letta_path, "settings.py")
    
    if not os.path.exists(settings_path):
        print(f"  ✗ Not found: {settings_path}")
        return False
    
    backup_file(settings_path)
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'venice_api_key' in content:
        print(f"  ⊙ Already patched: {settings_path}")
        return True
    
    # Find ModelSettings class and add Venice settings
    pattern = r'(class ModelSettings\(BaseSettings\):.*?)(    # .*?\n)'
    
    venice_settings = '''    # Venice
    venice_api_key: Optional[str] = None
    venice_base_url: str = "https://api.venice.ai/api/v1"

'''
    
    content = re.sub(pattern, r'\1' + venice_settings + r'\2', content, flags=re.DOTALL)
    
    with open(settings_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {settings_path}")
    return True


def patch_provider_init(letta_path):
    """Add Venice provider to __init__.py."""
    init_path = os.path.join(letta_path, "schemas", "providers", "__init__.py")
    
    if not os.path.exists(init_path):
        print(f"  ✗ Not found: {init_path}")
        return False
    
    backup_file(init_path)
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'VeniceProvider' in content:
        print(f"  ⊙ Already patched: {init_path}")
        return True
    
    # Add import
    content += '\nfrom letta.schemas.providers.venice import VeniceProvider\n'
    
    with open(init_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {init_path}")
    return True


def patch_llm_client(letta_path):
    """Add Venice client to LLM client factory."""
    llm_client_path = os.path.join(letta_path, "llm_api", "llm_client.py")
    
    if not os.path.exists(llm_client_path):
        print(f"  ✗ Not found: {llm_client_path}")
        return False
    
    backup_file(llm_client_path)
    
    with open(llm_client_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'VeniceClient' in content:
        print(f"  ⊙ Already patched: {llm_client_path}")
        return True
    
    # Add import
    if 'from letta.llm_api.groq_client import GroqClient' in content:
        content = content.replace(
            'from letta.llm_api.groq_client import GroqClient',
            'from letta.llm_api.groq_client import GroqClient\nfrom letta.llm_api.venice_client import VeniceClient'
        )
    
    # Add to factory
    content = content.replace(
        'elif llm_config.model_endpoint_type == "groq":\n        return GroqClient()',
        'elif llm_config.model_endpoint_type == "groq":\n        return GroqClient()\n    elif llm_config.model_endpoint_type == "venice":\n        return VeniceClient()'
    )
    
    with open(llm_client_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {llm_client_path}")
    return True


def patch_provider_manager(letta_path):
    """Add Venice provider to provider manager."""
    manager_path = os.path.join(letta_path, "services", "provider_manager.py")
    
    if not os.path.exists(manager_path):
        print(f"  ✗ Not found: {manager_path}")
        return False
    
    backup_file(manager_path)
    
    with open(manager_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'VeniceProvider' in content:
        print(f"  ⊙ Already patched: {manager_path}")
        return True
    
    # Add import
    content = content.replace(
        'from letta.schemas.providers.groq import GroqProvider',
        'from letta.schemas.providers.groq import GroqProvider\nfrom letta.schemas.providers.venice import VeniceProvider'
    )
    
    # Add to provider mapping
    content = content.replace(
        'ProviderType.groq: GroqProvider,',
        'ProviderType.groq: GroqProvider,\n        ProviderType.venice: VeniceProvider,'
    )
    
    with open(manager_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {manager_path}")
    return True


def patch_streaming_service(letta_path):
    """Add Venice to streaming service compatibility list."""
    streaming_path = os.path.join(letta_path, "services", "streaming_service.py")
    
    if not os.path.exists(streaming_path):
        print(f"  ✗ Not found: {streaming_path}")
        return False
    
    backup_file(streaming_path)
    
    with open(streaming_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if '"venice"' in content and '_is_model_compatible' in content:
        print(f"  ⊙ Already patched: {streaming_path}")
        return True
    
    # Add venice to compatible models list
    content = content.replace(
        '"chatgpt_oauth",\n        ]',
        '"chatgpt_oauth",\n            "venice",\n        ]'
    )
    
    with open(streaming_path, 'w') as f:
        f.write(content)
    
    print(f"  ✓ Patched: {streaming_path}")
    return True


def copy_venice_files(letta_path, patch_dir):
    """Copy Venice provider and client files."""
    # Copy venice.py to schemas/providers/
    src_provider = os.path.join(patch_dir, "patches", "venice.py")
    dst_provider = os.path.join(letta_path, "schemas", "providers", "venice.py")
    
    if os.path.exists(dst_provider):
        print(f"  ⊙ Already exists: {dst_provider}")
    else:
        shutil.copy2(src_provider, dst_provider)
        print(f"  ✓ Copied: {dst_provider}")
    
    # Copy venice_client.py to llm_api/
    src_client = os.path.join(patch_dir, "patches", "venice_client.py")
    dst_client = os.path.join(letta_path, "llm_api", "venice_client.py")
    
    if os.path.exists(dst_client):
        print(f"  ⊙ Already exists: {dst_client}")
    else:
        shutil.copy2(src_client, dst_client)
        print(f"  ✓ Copied: {dst_client}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python patch.py /path/to/letta")
        print("\nTo find your Letta installation:")
        print("  python -c \"import letta; print(letta.__path__[0])\"")
        sys.exit(1)
    
    letta_path = sys.argv[1]
    patch_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not os.path.exists(letta_path):
        print(f"Error: Letta path not found: {letta_path}")
        sys.exit(1)
    
    print(f"🔧 Patching Letta installation at: {letta_path}\n")
    
    print("📁 Copying Venice files...")
    copy_venice_files(letta_path, patch_dir)
    
    print("\n🔨 Applying patches...")
    patch_enums(letta_path)
    patch_llm_config(letta_path)
    patch_settings(letta_path)
    patch_provider_init(letta_path)
    patch_llm_client(letta_path)
    patch_provider_manager(letta_path)
    patch_streaming_service(letta_path)
    
    print("\n✅ Patch complete!")
    print("\nNext steps:")
    print("1. Set your Venice API key:")
    print("   export VENICE_API_KEY='your-key-here'")
    print("\n2. Enable run tracking (required for streaming):")
    print("   export LETTA_TRACK_AGENT_RUN='true'")
    print("\n3. Restart your Letta server")
    print("\n4. Try it out:")
    print("   letta run --model venice/qwen3-4b")


if __name__ == "__main__":
    main()
