#!/usr/bin/env python3
"""
Azure OpenAI Service Verification Script.
Validates live connectivity for text-embedding-3-small and gpt-4o deployments.
"""

import os
import sys
from pathlib import Path
import httpx

# Load environment from backend/.env.azure if available
ROOT_DIR = Path(__file__).resolve().parent.parent
env_azure_path = ROOT_DIR / "backend" / ".env.azure"
if env_azure_path.exists():
    with open(env_azure_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview").strip()

# Verification check for required configuration
if not endpoint:
    print("ERROR: AZURE_OPENAI_ENDPOINT is not set in environment or backend/.env.azure")
    sys.exit(1)

if not api_key:
    print("ERROR: AZURE_OPENAI_API_KEY is not set in environment or backend/.env.azure")
    sys.exit(1)

if not api_version:
    print("ERROR: AZURE_OPENAI_API_VERSION is not set in environment or backend/.env.azure")
    sys.exit(1)

# Normalize endpoint
base_endpoint = endpoint.rstrip("/")
headers = {
    "api-key": api_key,
    "Content-Type": "application/json",
}

print("=" * 60)
print("  AZURE OPENAI SERVICE VERIFICATION")
print(f"  Endpoint : {base_endpoint}")
print(f"  Version  : {api_version}")
print("=" * 60)

# ----------------------------------------------------------------------
# Test 1: text-embedding-3-small
# ----------------------------------------------------------------------
print("\n>>> Testing text-embedding-3-small...")
embed_url = f"{base_endpoint}/openai/deployments/text-embedding-3-small/embeddings?api-version={api_version}"
embed_body = {"input": "Atlas Copco centrifugal feed pump specification"}

try:
    embed_resp = httpx.post(embed_url, headers=headers, json=embed_body, timeout=15.0)
except Exception as e:
    print(f"ERROR: Connection failed for embeddings: {e}")
    sys.exit(1)

if embed_resp.status_code != 200:
    print(f"ERROR: Embedding request failed with HTTP {embed_resp.status_code}")
    sys.exit(1)

embed_data = embed_resp.json()
embeddings = embed_data.get("data", [])
if not embeddings or "embedding" not in embeddings[0]:
    print("ERROR: Invalid response structure from embedding endpoint.")
    sys.exit(1)

dim = len(embeddings[0]["embedding"])
if dim != 1536:
    print(f"ERROR: Expected embedding dimension 1536, but received {dim}.")
    sys.exit(1)

print(f"  [+] Embedding generation succeeded (dim={dim})")

# ----------------------------------------------------------------------
# Test 2: gpt-4o
# ----------------------------------------------------------------------
print("\n>>> Testing gpt-4o chat completions...")
chat_url = f"{base_endpoint}/openai/deployments/gpt-4o/chat/completions?api-version={api_version}"
chat_body = {
    "messages": [
        {"role": "system", "content": "You are an engineering assistant."},
        {"role": "user", "content": "What is 1 bar in psi? Answer with just the number."}
    ],
    "max_tokens": 50,
    "temperature": 0.0,
}

try:
    chat_resp = httpx.post(chat_url, headers=headers, json=chat_body, timeout=20.0)
except Exception as e:
    print(f"ERROR: Connection failed for chat completion: {e}")
    sys.exit(1)

if chat_resp.status_code != 200:
    print(f"ERROR: Chat completion request failed with HTTP {chat_resp.status_code}")
    sys.exit(1)

chat_data = chat_resp.json()
choices = chat_data.get("choices", [])
if not choices or "message" not in choices[0]:
    print("ERROR: Invalid response structure from chat completion endpoint.")
    sys.exit(1)

reply = choices[0]["message"].get("content", "").strip()
print(f"  [+] Chat completion succeeded (response: {reply})")

print("\n" + "=" * 60)
print("  ALL AZURE OPENAI VERIFICATION TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
sys.exit(0)
