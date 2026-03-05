from test.fakes import FakeInstagramPublisher, FakePostStorage

import pytest


@pytest.fixture
def fake_post_storage():
    return FakePostStorage()


@pytest.fixture
def fake_instagram_publisher():
    return FakeInstagramPublisher()


@pytest.fixture
def fake_instagram_publisher_unavailable():
    return FakeInstagramPublisher(connection_valid=False)
