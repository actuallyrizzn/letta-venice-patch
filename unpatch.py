#!/usr/bin/env python3
"""
Letta Venice AI Unpatch Script

Removes Venice AI provider support and restores original files.
"""

import os
import sys
import shutil
from pathlib import Path


def restore_backup(file_path):
    """Restore a file from its backup."""
    backup_path = f"{file_path}.backup"
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        os.remove(backup_path)
        print(f"  ✓ Restored: {file_path}")
        return True
    else:
        print(f"  ⊙ No backup found: {file_path}")
        return False


def remove_venice_files(letta_path):
    """Remove Venice provider and client files."""
    venice_provider = os.path.join(letta_path, "schemas", "providers", "venice.py")
    venice_client = os.path.join(letta_path, "llm_api", "venice_client.py")
    
    if os.path.exists(venice_provider):
        os.remove(venice_provider)
        print(f"  ✓ Removed: {venice_provider}")
    
    if os.path.exists(venice_client):
        os.remove(venice_client)
        print(f"  ✓ Removed: {venice_client}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python unpatch.py /path/to/letta")
        sys.exit(1)
    
    letta_path = sys.argv[1]
    
    if not os.path.exists(letta_path):
        print(f"Error: Letta path not found: {letta_path}")
        sys.exit(1)
    
    print(f"🔧 Unpatching Letta installation at: {letta_path}\n")
    
    print("📁 Removing Venice files...")
    remove_venice_files(letta_path)
    
    print("\n🔨 Restoring original files...")
    files_to_restore = [
        "schemas/enums.py",
        "schemas/llm_config.py",
        "settings.py",
        "schemas/providers/__init__.py",
        "llm_api/llm_client.py",
        "services/provider_manager.py",
        "services/streaming_service.py",
    ]
    
    for file_rel in files_to_restore:
        file_path = os.path.join(letta_path, file_rel)
        restore_backup(file_path)
    
    print("\n✅ Unpatch complete!")
    print("\nYour Letta installation has been restored to its original state.")


if __name__ == "__main__":
    main()
