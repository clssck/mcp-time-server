# Time Server

[![smithery badge](https://smithery.ai/badge/@clssck/mcp-time-server)](https://smithery.ai/server/@clssck/mcp-time-server)
![MCP](https://img.shields.io/badge/MCP-Protocol-blue)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

An MCP server for timezone conversions and time-related operations, built with the Model Context Protocol standards.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [License](#license)

## Features

- Get current time in any timezone
- Convert time between timezones
- Built with MCP protocol standards
- Type-safe Python implementation
- RESTful API endpoints
- Comprehensive error handling
- Timezone database integration

## Installation

### Installing via Smithery

To install Time Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@clssck/mcp-time-server):

```bash
npx -y @smithery/cli install @clssck/mcp-time-server --client claude
```

### Manual Installation

```bash
pip install .
```

## Usage

Start the server:

```bash
python -m time_server
```

## API Documentation

### Tools

#### `get_current_time`

Get current time in a specific timezone

**Parameters:**

- `timezone`: string - IANA timezone identifier (e.g. "America/New_York")

**Returns:**

- Current time in ISO 8601 format

#### `convert_time`

Convert time between timezones

**Parameters:**

- `time`: string - Time to convert in ISO 8601 format
- `from_timezone`: string - Source timezone
- `to_timezone`: string - Target timezone

**Returns:**

- Converted time in ISO 8601 format

## Development

Install development dependencies:

```bash
pip install -e .[dev]
```

Run tests:

```bash
pytest
```

Check code quality:

```bash
ruff check .
mypy src
```

## Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

MIT
