import os

import pytest


os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://games_user:postgres_password@127.0.0.1:25432/games_test",
)

from app import app  # noqa: E402
from datasource.database import db  # noqa: E402


@pytest.fixture
def clean_database():
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
