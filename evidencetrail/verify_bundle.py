"""Run with python -m evidencetrail.verify_bundle path/to/audit.zip."""
import argparse
import json
from pathlib import Path
import sys
from .bundle import MAX_BUNDLE_BYTES, verify_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        with args.bundle.open("rb") as stream:
            content = stream.read(MAX_BUNDLE_BYTES + 1)
        report = verify_bundle(content)
    except (ValueError, OSError) as error:
        print(f"Verification stopped: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
