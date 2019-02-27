from bocadillo.fixtures import Store


def test_name_is_function_name_by_default(store: Store):
    @store.fixture
    def example():
        pass

    assert example.name == "example"


def test_if_name_given_then_used(store: Store):
    @store.fixture(name="an_example")
    def example():
        pass

    assert example.name == "an_example"
