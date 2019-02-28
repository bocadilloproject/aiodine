# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[unreleased]: https://github.com/bocadilloproject/aiodine/compare/v0.1.2...HEAD
[v0.1.2]: https://github.com/bocadilloproject/aiodine/compare/v0.1.1...v0.1.2
[v0.1.1]: https://github.com/bocadilloproject/aiodine/compare/v0.1.0...v0.1.1
[v0.1.0]: https://github.com/bocadilloproject/aiodine/releases/tag/v0.1.0
