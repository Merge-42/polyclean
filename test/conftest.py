from test.fakes import FakeInstagramPublisher, FakePostStorage

import pytest


@pytest.fixture
def fake_post_storage() -> FakePostStorage:
    return FakePostStorage()


@pytest.fixture
def fake_instagram_publisher() -> FakeInstagramPublisher:
    return FakeInstagramPublisher()


@pytest.fixture
def fake_instagram_publisher_unavailable() -> FakeInstagramPublisher:
    return FakeInstagramPublisher(connection_valid=False)
