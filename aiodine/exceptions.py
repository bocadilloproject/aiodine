class AiodineException(Exception):
    """Base exceptions for the aiodine package."""


class ConsumerDeclarationError(AiodineException):
    """Base exception for when a consumer is ill-declared."""


class ProviderDeclarationError(AiodineException):
    """Base exception for when a provider is ill-declared."""


class RecursiveProviderError(ProviderDeclarationError):
    """Raised when two providers depend on each other."""

    def __init__(self, first: str, second: str):
        message = (
            "recursive provider detected: "
            f"{first} and {second} depend on each other."
        )
        super().__init__(message)


class UnknownScope(AiodineException):
    """Raised when an unknown scope is used."""
