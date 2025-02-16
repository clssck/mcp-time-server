# Time Server

An MCP server for timezone conversions and time-related operations.

## Features

- Get current time in any timezone
- Convert time between timezones
- Built with MCP protocol standards
- Type-safe Python implementation

## Installation

```bash
pip install .
```

## Usage

Start the server:

```bash
python -m time_server
```

## API

### Tools

- `get_current_time`: Get current time in a specific timezone
- `convert_time`: Convert time between timezones

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

## License

MIT
