"""Demo-only, explicit migration target selection.

Initial phase intentionally contains exactly two shards (A and B).
Target C migrations run only after the live C database is created.
Never use this entrypoint against an existing non-demo deployment.
"""
from __future__ import annotations

import argparse
import os

from scripts.apply_migrations import TARGETS, apply_target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--targets', nargs='+', required=True,
                        choices=[x[0] for x in TARGETS])
    requested = parser.parse_args().targets
    if len(set(requested)) != len(requested):
        raise SystemExit('duplicate database targets are not permitted')
    for name, env, folder in TARGETS:
        if name in requested:
            if not os.getenv(env):
                raise RuntimeError(f'Missing connection string: {env}')
            apply_target(name, os.environ[env], folder)
    print('VIDEO DEMO MIGRATIONS: ' + ', '.join(requested) + ' COMPLETE', flush=True)


if __name__ == '__main__':
    main()
