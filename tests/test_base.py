import pytest


@pytest.fixture
def context():
    return {
        "project_name": "My Brick Test",
        "project_slug": "my_brick_test",
        "author_name": "Brick Top",
        "email": "top@brick.com",
        "version": "0.1.0",
        "timezone": "UTC",
    }


def test_default_configuration(cookies, context):
    result = cookies.bake(extra_context=context)
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.name == context["project_slug"]
    assert result.project_path.is_dir()
