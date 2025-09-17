import pytest
from pathlib import Path
from collections.abc import Iterable
from binaryornot.check import is_binary
import re

PATTERN = r"{{(\s?cookiecutter)[.](.*?)}}"
RE_OBJ = re.compile(PATTERN)


@pytest.fixture
def context():
    return {
        "project_name": "My Brick Test",
        "project_slug": "my_brick_test",
        "author_name": "Brick Top",
        "email": "top@brick.com",
        "timezone": "UTC",
    }


def build_files_list(base_path: Path):
    """Build a list containing absolute paths to the generated files."""
    excluded_dirs = {".venv", "__pycache__"}

    f = []
    for dirpath, subdirs, files in base_path.walk():
        subdirs[:] = [d for d in subdirs if d not in excluded_dirs]

        f.extend(dirpath / file_path for file_path in files)
    return f


def check_paths(paths: Iterable[Path]):
    """Method to check all paths have correct substitutions."""
    # Assert that no match is found in any of the files
    for path in paths:
        if is_binary(str(path)):
            continue

        for line in path.open():
            match = RE_OBJ.search(line)
            assert match is None, f"cookiecutter variable not replaced in {path}"


def test_project_generation(cookies, context):
    """Test that project is generated and fully rendered."""

    result = cookies.bake(extra_context={**context})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.name == context["project_slug"]
    assert result.project_path.is_dir()

    paths = build_files_list(result.project_path)
    assert paths
    check_paths(paths)


def test_config_file_creation(cookies, context):
    result = cookies.bake(extra_context=context)

    # Assert post-gen hook created the YAML config file
    config_path = result.project_path / f"{context['project_slug']}-config.yaml"
    assert config_path.exists(), "Expected config file to be created by post_gen hook"

    contents = config_path.read_text(encoding="utf-8")
    # Verify key contents from context are present and correctly quoted
    for key, value in context.items():
        assert f'{key}: "{value}"' in contents
