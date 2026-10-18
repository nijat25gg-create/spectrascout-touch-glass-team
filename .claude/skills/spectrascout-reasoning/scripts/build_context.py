"""Build a reasoning addendum; never replace or load the host system prompt."""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = {
    "chemistry": "chemistry-foundations.md",
    "domain": "domain-checks.md",
    "experiment": "experiment-design.md",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, choices=("a", "b"))
    parser.add_argument(
        "--include", action="append", default=[], choices=tuple(REFERENCES),
        help="Explicit caller selection; no references are included by default.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    core = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    # Frontmatter is discovery metadata, not runtime instructions.
    body = core.split("---", 2)[2].strip()
    parts = [body, f"Caller-selected assessment mode: method {args.method.upper()}."]
    for name in dict.fromkeys(args.include):
        text = (ROOT / "references" / REFERENCES[name]).read_text(encoding="utf-8")
        parts.append(f"Optional domain background ({name}):\n{text}")
    output = args.output.resolve()
    # Keep generated prompts outside the reusable package and do not overwrite inputs.
    if output == ROOT or ROOT in output.parents:
        parser.error("Write generated context outside the skill package.")
    if output.exists():
        parser.error("Output already exists; choose a new output path.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write("\n\n".join(parts) + "\n")


if __name__ == "__main__":
    main()
