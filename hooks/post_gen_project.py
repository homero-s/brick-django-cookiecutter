import json
from pathlib import Path
import shutil
import subprocess
import sys


def _yaml_escape(value: str) -> str:
    # Quote all values to keep YAML simple and robust.
    s = str(value)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def create_config_file() -> None:
    # cookiecutter renders this file; use the provided context via jsonify.
    context = json.loads("""{{ cookiecutter | jsonify }}""")

    # Keep filename based on project_slug per requirements
    project_slug = context.get("project_slug", "project")
    outfile = Path(f"{project_slug}-config.yaml")

    # Only include user/context keys that do not start with underscore.
    lines = [
        f"{k}: {_yaml_escape(v)}"
        for k, v in context.items()
        if not str(k).startswith("_")
    ]

    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")


def convert_env_example() -> None:
    """Rename .env.example to .env and remove the example file."""
    example_path = Path(".env.example")
    if not example_path.exists():
        return
    dest_path = Path(".env")
    if dest_path.exists():
        try:
            example_path.unlink()
        except OSError:
            pass
        return
    try:
        example_path.rename(dest_path)
    except OSError:
        dest_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            example_path.unlink()
        except OSError:
            pass


def setup_dependencies():
    print("Installing python dependencies using uv...")

    # Build a trimmed down Docker image add dependencies with uv
    uv_docker_image_path = Path("compose/uv/Dockerfile")
    uv_image_tag = "cookiecutter-django-uv-runner:latest"
    try:
        subprocess.run(  # noqa: S603
            [  # noqa: S607
                "docker",
                "build",
                "-t",
                uv_image_tag,
                "-f",
                str(uv_docker_image_path),
                "-q",
                ".",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}", file=sys.stderr)
        sys.exit(1)

    # Use Docker to run the uv command
    uv_cmd = ["docker", "run", "--rm", "-v", "./app:/app", uv_image_tag, "uv"]

    # Install dependencies
    try:
        subprocess.run(
            [*uv_cmd, "add", "--no-sync", "-r", "requirements.txt"], check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error installing production dependencies: {e}", file=sys.stderr)
        sys.exit(1)

    print("Setup complete!")


def remove_uv_compose_dir() -> None:
    """Remove the compose/uv directory and its contents if present."""
    uv_dir = Path("compose") / "uv"
    if not uv_dir.exists():
        return
    if uv_dir.is_dir():
        try:
            shutil.rmtree(uv_dir)
        except OSError:
            pass
    else:
        try:
            uv_dir.unlink()
        except OSError:
            pass


def main() -> None:
    create_config_file()

    convert_env_example()

    setup_dependencies()

    remove_uv_compose_dir()


if __name__ == "__main__":
    main()
