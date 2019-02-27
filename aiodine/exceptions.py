class ProviderDeclarationError(Exception):
    """Base exception for situations when a provider was ill-declared."""


class RecursiveProviderError(ProviderDeclarationError):
    """Raised when two providers depend on each other."""

    def __init__(self, first: str, second: str):
        message = (
            "recursive provider detected: "
            f"{first} and {second} depend on each other."
        )
        super().__init__(message)
