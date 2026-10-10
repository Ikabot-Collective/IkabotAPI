import importlib.util
import re
from pathlib import Path

import pytest

from apps import __version__


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "bump_version", ROOT / ".github" / "scripts" / "bump_version.py"
)
bump_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump_module)


@pytest.fixture
def release_tree(tmp_path):
    (tmp_path / "apps").mkdir()
    for relative in ("apps/__init__.py", "pyproject.toml"):
        (tmp_path / relative).write_bytes((ROOT / relative).read_bytes())
    return tmp_path


def test_version_is_consistent_in_package_and_api(client):
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^version = "([^"]+)"$', metadata, re.MULTILINE)[1] == __version__
    assert client.get("/health").json()["version"] == __version__
    assert client.get("/openapi.json").json()["info"]["version"] == __version__
    assert f"v{__version__}" in client.get("/").text


def test_bump_updates_runtime_and_metadata_without_changing_dependencies(release_tree):
    metadata_path = release_tree / "pyproject.toml"
    original_metadata = metadata_path.read_text(encoding="utf-8")
    next_version = f"{int(__version__.split('.')[0]) + 1}.0.0"

    bump_module.bump_version(release_tree, next_version)

    namespace = {}
    exec((release_tree / "apps/__init__.py").read_text(encoding="utf-8"), namespace)
    assert namespace["__version__"] == next_version
    assert metadata_path.read_text(encoding="utf-8") == original_metadata.replace(
        f'version = "{__version__}"', f'version = "{next_version}"', 1
    )
    # Retrying after a failed build must not require a second version bump.
    updated_files = [
        (release_tree / relative).read_bytes()
        for relative in ("apps/__init__.py", "pyproject.toml")
    ]
    bump_module.bump_version(release_tree, next_version)
    assert updated_files == [
        (release_tree / relative).read_bytes()
        for relative in ("apps/__init__.py", "pyproject.toml")
    ]


@pytest.mark.parametrize("version", ["v3.0.0", "3.0", "03.0.0", "3.0.0-rc.1", "3.0.0\n", "0.0.0"])
def test_invalid_or_older_version_does_not_modify_files(release_tree, version):
    paths = [release_tree / "apps/__init__.py", release_tree / "pyproject.toml"]
    originals = [path.read_bytes() for path in paths]

    with pytest.raises(ValueError):
        bump_module.bump_version(release_tree, version)

    assert [path.read_bytes() for path in paths] == originals


def test_invalid_metadata_does_not_partially_update_runtime_version(release_tree):
    runtime_path = release_tree / "apps/__init__.py"
    original_runtime = runtime_path.read_bytes()
    (release_tree / "pyproject.toml").write_text("[tool.poetry]\n", encoding="utf-8")

    with pytest.raises(ValueError):
        bump_module.bump_version(release_tree, "999.0.0")

    assert runtime_path.read_bytes() == original_runtime
