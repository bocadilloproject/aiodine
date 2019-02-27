from aiodine import Store, Provider


def test_at_provider_returns_a_provider_object(store: Store):
    @store.provider
    def example():
        pass

    assert isinstance(example, Provider)
