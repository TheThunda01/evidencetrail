"""Export the editable reviewer-comparison diagram with draw.io Desktop."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drawio", default="draw.io", help="draw.io executable or full path")
    args = parser.parse_args()
    source = ROOT / "docs/diagrams/reviewer-comparison.drawio"
    for extension in ("svg", "png"):
        output = source.with_suffix("." + extension)
        subprocess.run([args.drawio, "--export", "--format", extension, "--border", "20",
                        "--output", str(output), str(source)], check=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"Export missing: {output}")


if __name__ == "__main__":
    main()
