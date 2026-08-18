#!/usr/bin/env python3
"""
Download BERT security models into HF_HOME at Docker image build time.

Runtime loads from the same cache, so the first /ask does not hit the Hub.
Embeddings stay on OpenAI (1536-d); only the security gate uses local HF weights.
"""

from __future__ import annotations

from huggingface_hub import snapshot_download

SECURITY_MODELS = (
    "unitary/toxic-bert",
    "typeform/distilbert-base-uncased-mnli",
)


def main() -> None:
    for repo_id in SECURITY_MODELS:
        print(f"Downloading {repo_id} ...")
        snapshot_download(repo_id=repo_id)
        print(f"  cached {repo_id}")


if __name__ == "__main__":
    main()
