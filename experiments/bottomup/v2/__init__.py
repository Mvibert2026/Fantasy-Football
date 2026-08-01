"""Ranking v2 — the independent bottom-up version (Fable build mandate B1).

Registered: docs/ranking/factor-campaign-manifest/batch-B1.md, BEFORE any arm was
fitted. Config: experiments/bottomup/ranking_versions/v2.json.

ADR-069 binds everything in this package: the ordering path reads no consensus,
no ADP, no ECR anywhere; projections are stat lines; points come from applying a
league scoring config to the stat lines; steering is absolute quality against
realised outcomes on seasons through 2024. The 2025 holdout is sealed and the
panel gates enforce it structurally.
"""
