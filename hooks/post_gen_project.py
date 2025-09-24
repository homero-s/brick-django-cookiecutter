import json
from pathlib import Path
import shutil
import subprocess
import random
import sys
import string

try:
    # Inspired by
    # https://github.com/django/django/blob/main/django/utils/crypto.py
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    using_sysrandom = False


DEBUG = True if "{{ cookiecutter.env_type }}" == "dev" else False
ENV_PATH = Path(".env")


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
    if ENV_PATH.exists():
        try:
            example_path.unlink()
        except OSError:
            pass
        return
    try:
        example_path.rename(ENV_PATH)
    except OSError:
        ENV_PATH.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
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
        print(f"Error installing dependencies: {e}", file=sys.stderr)
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


def generate_random_string(
    length, using_digits=False, using_ascii_letters=False, using_punctuation=False
):  # noqa: FBT002
    """
    Example:
        opting out for 50 symbol-long, [a-z][A-Z][0-9] string
        would yield log_2((26+26+50)^50) ~= 334 bit strength.
    """
    if not using_sysrandom:
        return None

    symbols = []
    if using_digits:
        symbols += string.digits
    if using_ascii_letters:
        symbols += string.ascii_letters
    if using_punctuation:
        all_punctuation = set(string.punctuation)
        # These symbols can cause issues in environment variables
        unsuitable = {"'", '"', "\\", "$", "#"}
        suitable = all_punctuation.difference(unsuitable)
        symbols += "".join(suitable)
    return "".join([random.choice(symbols) for _ in range(length)])


def set_env_var(file_path: Path, env_var, value=None, formatted=None, *args, **kwargs):
    if value is None:
        random_string = generate_random_string(*args, **kwargs)
        if random_string is None:
            print(
                "We couldn't find a secure pseudo-random number generator on your "
                f"system. Please, make sure to manually set {env_var} later.",
            )
            random_string = env_var
        if formatted is not None:
            random_string = formatted.format(random_string)
        value = random_string

    with file_path.open("r+") as f:
        file_contents = f.read().replace(env_var, value)
        f.seek(0)
        f.write(file_contents)
        f.truncate()

    return value


def set_django_secret_key():
    return set_env_var(
        ENV_PATH,
        "supersecret",
        length=64,
        using_digits=True,
        using_ascii_letters=True,
        using_punctuation=True,
    )


def generate_postgres_user():
    if DEBUG:
        return "debug"
    else:
        return generate_random_string(length=32, using_ascii_letters=True)


def set_postgres_user():
    pg_user = generate_postgres_user()
    return set_env_var(ENV_PATH, "changeme_pg_user", value=pg_user)


def set_postgres_password(value=None):
    if DEBUG:
        value = "debug"
    return set_env_var(
        ENV_PATH,
        "changeme_pg_pw",
        value=value,
        length=64,
        using_digits=True,
        using_ascii_letters=True,
    )


def main() -> None:
    create_config_file()
    convert_env_example()
    setup_dependencies()
    remove_uv_compose_dir()
    set_django_secret_key()

    set_postgres_user()
    set_postgres_password()


if __name__ == "__main__":
    main()
