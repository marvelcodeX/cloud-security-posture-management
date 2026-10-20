"""Throwaway file to deliberately fail the Bandit required check.

Exists only to verify branch protection actually blocks a PR with a failing
required check (Wave D M4 deliverable). Delete this file instead of merging
it; this PR should be closed, not merged.
"""

import subprocess


def run_unsafe_command(user_input: str) -> None:
    subprocess.call(user_input, shell=True)
