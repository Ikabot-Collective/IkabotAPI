"""Update the runtime and Poetry versions together for a stable release."""

import argparse
import re
from pathlib import Path


VERSION_PATTERN = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def bump_version(root: Path, version: str) -> None:
    if not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError("Use a stable version such as 2.1.0, without the v prefix")

    replacements = (
        (root / "apps" / "__init__.py", r'^__version__ = "([^"]+)"$', "__version__"),
        (root / "pyproject.toml", r'^version = "([^"]+)"$', "version"),
    )
    updates = []
    for path, pattern, key in replacements:
        content = path.read_text(encoding="utf-8")
        matches = re.findall(pattern, content, flags=re.MULTILINE)
        if len(matches) != 1 or not re.fullmatch(VERSION_PATTERN, matches[0]):
            raise ValueError(f"Expected exactly one stable {key} in {path}")
        if tuple(map(int, version.split("."))) < tuple(map(int, matches[0].split("."))):
            raise ValueError(f"Cannot downgrade {path.name} from {matches[0]} to {version}")
        updated = re.sub(pattern, f'{key} = "{version}"', content, flags=re.MULTILINE)
        updates.append((path, updated))

    # Validate both files before modifying either of them.
    for path, content in updates:
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    args = parser.parse_args()
    try:
        bump_version(Path(__file__).resolve().parents[2], args.version)
    except ValueError as error:
        parser.error(str(error))
