import pytest


@pytest.fixture
def context():
    return {
        "project_name": "My Brick Test",
        "project_slug": "my_brick_test",
        "author_name": "Brick Top",
        "email": "top@brick.com",
        "timezone": "UTC",
    }


def test_default_configuration(cookies, context):
    result = cookies.bake(extra_context=context)
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.name == context["project_slug"]
    assert result.project_path.is_dir()

    # Assert post-gen hook created the YAML config file
    config_path = result.project_path / f"{context['project_slug']}-config.yaml"
    assert config_path.exists(), "Expected config file to be created by post_gen hook"

    contents = config_path.read_text(encoding="utf-8")
    # Verify key contents from context are present and correctly quoted
    for key, value in context.items():
        assert f'{key}: "{value}"' in contents
