# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

Initial release.

### Added

- Sync/async providers.
  - Providers are named after their function, unless `name` is given.
- Sync/async consumers.
- `session` and `app` scopes.
- Session-scoped generator providers.
- Lazy async providers (session-scoped only).
- Provider discovery: `@aiodine.provider`, `providerconf.py`, `discover_providers()`.
- Nested providers: providers that consume other providers.
