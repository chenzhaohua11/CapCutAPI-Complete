# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Environment variable configuration support (.env)
- Enhanced security configuration options
- Rate limiting functionality
- Structured logging with rotation
- Health check endpoint (/health)
- Input validation and sanitization
- Docker health checks

### Changed
- Unified dependency management across requirements files
- Improved configuration file structure
- Enhanced error handling and logging
- Updated security best practices

### Security
- Removed hardcoded credentials from configuration
- Added CORS configuration options
- Implemented request rate limiting
- Enhanced input validation

## [1.0.0] - 2024-01-15

### Added
- Initial release of CapCutAPI
- Core video editing functionality
- Draft management system
- Audio/video track support
- Effects and transitions
- Text and subtitle support
- Image and sticker integration
- Keyframe animations
- MCP protocol support
- RESTful API endpoints
- Docker containerization
- OSS cloud storage integration
- Batch processing capabilities

### Features
- Real-time preview generation
- Cloud-based rendering
- Local development environment
- Comprehensive documentation
- Example implementations
- Cross-platform support (Windows/Linux)

## [1.0.0-beta] - 2023-12-01

### Added
- Beta release with core functionality
- Basic video editing features
- Simple API endpoints
- Basic Docker support

[Unreleased]: https://github.com/ashreo/CapCutAPI/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ashreo/CapCutAPI/compare/v1.0.0-beta...v1.0.0
[1.0.0-beta]: https://github.com/ashreo/CapCutAPI/releases/tag/v1.0.0-beta