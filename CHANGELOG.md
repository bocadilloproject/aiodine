# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v1.2.8] - 2019-09-12

### Added

- Contributing guidelines.

### Changed

- Recommend users to pin dependency to `==1.*`.

## [v1.2.7] - 2019-06-19

### Fixed

- Passing providers as strings to `@useprovider` is now lazy: providers will be resolved at runtime.

### Changed

- Passing an unknown provider name to `@useprovider` now results in a `ProviderDoesNotExist` exception raised when calling the consumer.

## [v1.2.6] - 2019-05-08

### Fixed

- Session-scoped async generator providers were not correctly handled: they returned the async generator instead of setting and cleaning it up. This has been fixed!

## [v1.2.5] - 2019-03-30

### Fixed

- Fix regression on instance method consumers.

## [v1.2.4] - 2019-03-30

### Added

- Add support for class-based consumers (must implement `.__call__()`).

## [v1.2.3] - 2019-03-29

### Added

- Add support for keyword-only parameters in consumers.

## [v1.2.2] - 2019-03-24

### Fixed

- Previously, `ImportError` exceptions were silenced when discovering default providers (e.g. in `providerconf.py`). This lead to unexpected behavior when the providers module exists but raises an `ImportError` itself. We now correctly check whether the providers module _exists_ before importing it normally.

## [v1.2.1] - 2019-03-15

### Fixed

- The order of arguments passed to a consumer is now preserved. It was previously reversed.

## [v1.2.0] - 2019-03-15

### Fixed

- Providers can now be overridden regardless of their declaration order with respect to consumers that use them. Previously, a provider could only be overridden _before_ it was used in a consumer, which was of limited use.

## [v1.1.1] - 2019-03-14

### Fixed

- A bug led `partial` consumer functions wrapping a coroutine function to not be called properly when awaiting the aiodine consumer. This has been fixed.

## [v1.1.0] - 2019-03-09

### Added

- Context providers: provide context-local variables to consumers.

## [v1.0.1] - 2019-03-03

### Fixed

- Guarantee that finalization code of generator providers gets executed even if an exception occurs in the consumer.

## [v1.0.0] - 2019-03-03

### Added

- Use providers whose return value is not important via the `@useprovider` decorator.
- Auto-used providers — activated without having to declare them in consumer parameters.

### Fixed

- Providers declared as keyword-only parameters in consumers are now properly injected.
- Require that Python 3.6+ is installed at the package level.

## [v0.2.0] - 2019-03-02

### Added

- Session-scoped generator providers, both sync and async.
- Documentation for the factory provider pattern.
- Session enter/exit utils: `store.enter_session()`, `store.exit_session()`, `async with store.session()`. Allows to manually trigger the setup/cleanup of session-scoped providers.

## [v0.1.3] - 2019-03-01

### Fixed

- Parameters are now correctly resolved regardless of the positioning of provider parameters relative to non-provider parameters.

## [v0.1.2] - 2019-02-28

### Fixed

- Fix an issue that occured when a consumer was an instance of `functools.partial`.

## [v0.1.1] - 2019-02-28

### Added

- Scope aliases: allows a store's `@provider` decorator to accept a scope equivalent to (but different from) one of `function` or `session`. For example: `app -> session`.
- The `providers_module` is now configurable on `Store`.
- The (non-aliased) `default_scope` is now configurable on `Store`.

### Changed

- `Store.empty` is now a callable instead of a property.

## [v0.1.0] - 2019-02-28

Initial release.

### Added

- Sync/async providers.
  - Providers are named after their function, unless `name` is given.
- Sync/async consumers.
- `function` and `session` scopes.
- Session-scoped generator providers.
- Lazy async providers (function-scoped only).
- Provider discovery: `@aiodine.provider`, `providerconf.py`, `discover_providers()`.
- Nested providers: providers can consume other providers.
- Use the `aiodine` module directly or create a separate `Store`.

[unreleased]: https://github.com/bocadilloproject/aiodine/compare/v1.2.8...HEAD
[v1.2.8]: https://github.com/bocadilloproject/aiodine/compare/v1.2.7...v1.2.8
[v1.2.7]: https://github.com/bocadilloproject/aiodine/compare/v1.2.6...v1.2.7
[v1.2.6]: https://github.com/bocadilloproject/aiodine/compare/v1.2.5...v1.2.6
[v1.2.5]: https://github.com/bocadilloproject/aiodine/compare/v1.2.4...v1.2.5
[v1.2.4]: https://github.com/bocadilloproject/aiodine/compare/v1.2.3...v1.2.4
[v1.2.3]: https://github.com/bocadilloproject/aiodine/compare/v1.2.2...v1.2.3
[v1.2.2]: https://github.com/bocadilloproject/aiodine/compare/v1.2.1...v1.2.2
[v1.2.1]: https://github.com/bocadilloproject/aiodine/compare/v1.2.0...v1.2.1
[v1.2.0]: https://github.com/bocadilloproject/aiodine/compare/v1.1.1...v1.2.0
[v1.1.1]: https://github.com/bocadilloproject/aiodine/compare/v1.1.0...v1.1.1
[v1.1.0]: https://github.com/bocadilloproject/aiodine/compare/v1.0.1...v1.1.0
[v1.0.1]: https://github.com/bocadilloproject/aiodine/compare/v1.0.0...v1.0.1
[v1.0.0]: https://github.com/bocadilloproject/aiodine/compare/v0.2.0...v1.0.0
[v0.2.0]: https://github.com/bocadilloproject/aiodine/compare/v0.1.3...v0.2.0
[v0.1.3]: https://github.com/bocadilloproject/aiodine/compare/v0.1.2...v0.1.3
[v0.1.2]: https://github.com/bocadilloproject/aiodine/compare/v0.1.1...v0.1.2
[v0.1.1]: https://github.com/bocadilloproject/aiodine/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/bocadilloproject/aiodine/releases/tag/v0.1.0
