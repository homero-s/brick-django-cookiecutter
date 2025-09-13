import json
from pathlib import Path


def _yaml_escape(value: str) -> str:
    # Quote all values to keep YAML simple and robust.
    s = str(value)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def main() -> None:
    # cookiecutter renders this file; use the provided context via jsonify.
    context = json.loads("""{{ cookiecutter | jsonify }}""")

    project_slug = context.get("project_slug", "project")
    outfile = Path(f"{project_slug}-config.yaml")

    # Only include user/context keys that do not start with underscore.
    lines = [
        f"{k}: {_yaml_escape(v)}"
        for k, v in context.items()
        if not str(k).startswith("_")
    ]

    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
