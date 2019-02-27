from aiodine import Store, Fixture


def test_at_fixture_returns_a_fixture_object(store: Store):
    @store.fixture
    def example():
        pass

    assert isinstance(example, Fixture)
