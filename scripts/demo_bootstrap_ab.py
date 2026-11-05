"""Schema + all-account initial seed for the A/B-only video phase."""
from __future__ import annotations

import os

from scripts.apply_migrations import TARGETS, apply_target
from scripts.demo_seed_full_ranges import seed_full_ranges


def main() -> None:
    for name, variable, folder in TARGETS:
        if name in ('metadata','shard-a','shard-b'):
            apply_target(name, os.environ[variable], folder)
    seed_full_ranges()
    print('VIDEO INITIAL PHASE: A/B MIGRATIONS AND FULL RANGE SEED COMPLETE',flush=True)


if __name__=='__main__':
    main()
