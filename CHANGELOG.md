# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[unreleased]: https://github.com/bocadilloproject/aiodine/compare/v1.0.0...HEAD
[v1.0.0]: https://github.com/bocadilloproject/aiodine/compare/v0.2.0...v1.0.0
[v0.2.0]: https://github.com/bocadilloproject/aiodine/compare/v0.1.3...v0.2.0
[v0.1.3]: https://github.com/bocadilloproject/aiodine/compare/v0.1.2...v0.1.3
[v0.1.2]: https://github.com/bocadilloproject/aiodine/compare/v0.1.1...v0.1.2
[v0.1.1]: https://github.com/bocadilloproject/aiodine/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/bocadilloproject/aiodine/releases/tag/v0.1.0
