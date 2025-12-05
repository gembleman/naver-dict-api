# Naver Dictionary API Client

A Python library for accessing Naver Dictionary APIs with support for multiple language dictionaries including Hanja (漢字), Korean, English, Japanese, Chinese, and more.

## Features

- **Multi-language Support**: Access 14+ different Naver dictionaries (Hanja, Korean, English, Japanese, Chinese, German, French, Spanish, Russian, Vietnamese, Italian, Thai, Indonesian, Uzbek)
- **Two Search Modes**: Simple mode for quick lookups, detailed mode for comprehensive results
- **Fast & Reliable**: Built with `curl-cffi` for robust HTTP requests with browser impersonation
- **Type-Safe**: Full type hints for better IDE support and code reliability
- **Well-Tested**: Comprehensive test coverage with both unit and integration tests

## Installation

```bash
pip install naver-dict-api
```

## Quick Start

### Basic Usage

```python
from naver_dict_api import search_dict, DictType

# Search Hanja (Chinese characters)
entry = search_dict("漢", DictType.HANJA)
if entry:
    print(f"Word: {entry.word}")
    print(f"Reading: {entry.reading}")
    print(f"Meanings: {', '.join(entry.meanings)}")

# Search Korean
entry = search_dict("안녕", DictType.KOREAN)

# Search English
entry = search_dict("hello", DictType.ENGLISH)
```

### Using the Client Class

```python
from naver_dict_api import NaverDictClient, DictType, SearchMode

# Create a client instance
client = NaverDictClient(
    dict_type=DictType.HANJA,
    search_mode=SearchMode.DETAILED
)

# Search for a word
entry = client.search("漢")
if entry:
    print(entry.to_dict())
```

## Supported Dictionary Types

```python
from naver_dict_api import DictType

DictType.HANJA        # 漢字 (Chinese characters)
DictType.KOREAN       # 국어 (Korean)
DictType.ENGLISH      # 영어 (English)
DictType.JAPANESE     # 일본어 (Japanese)
DictType.CHINESE      # 중국어 (Chinese)
DictType.GERMAN       # 독일어 (German)
DictType.FRENCH       # 프랑스어 (French)
DictType.SPANISH      # 스페인어 (Spanish)
DictType.RUSSIAN      # 러시아어 (Russian)
DictType.VIETNAMESE   # 베트남어 (Vietnamese)
DictType.ITALIAN      # 이탈리아어 (Italian)
DictType.THAI         # 태국어 (Thai)
DictType.INDONESIAN   # 인도네시아어 (Indonesian)
DictType.UZBEK        # 우즈베키스탄어 (Uzbek)
```

## API Reference

### `search_dict()`

Convenience function for quick dictionary lookups.

```python
def search_dict(
    query: str,
    dict_type: DictType = DictType.HANJA,
    search_mode: SearchMode = SearchMode.SIMPLE,
    *,
    impersonate: BrowserTypeLiteral | None = "chrome136",
    timeout: int | None = None,
) -> DictEntry | None
```

**Parameters:**
- `query`: Search term
- `dict_type`: Dictionary type (default: HANJA)
- `search_mode`: Search mode (default: SIMPLE)
- `impersonate`: Browser to impersonate (default: "chrome136")
- `timeout`: Request timeout in seconds (default: 30)

**Returns:** `DictEntry` object or `None` if not found

### `NaverDictClient`

Main client class for dictionary searches.

```python
client = NaverDictClient(
    dict_type=DictType.HANJA,
    search_mode=SearchMode.SIMPLE,
    impersonate="chrome136",
    timeout=30
)

entry = client.search("query")
```

### `DictEntry`

Data class representing a dictionary entry.

**Attributes:**
- `word`: The word or character
- `reading`: Pronunciation or reading
- `meanings`: List of meanings/definitions
- `entry_id`: Unique entry identifier
- `dict_type`: Dictionary type code

**Methods:**
- `to_dict()`: Convert to dictionary format

## Error Handling

The library provides specific exceptions for different error cases:

```python
from naver_dict_api import (
    NaverDictError,      # Base exception
    NetworkError,        # Network-related errors
    ParseError,          # JSON parsing errors
    InvalidResponseError # Invalid API response
)

try:
    entry = search_dict("test")
except NetworkError:
    print("Network connection failed")
except ParseError:
    print("Failed to parse response")
except InvalidResponseError:
    print("Invalid response from API")
```

## Requirements

- Python ≥ 3.13
- curl-cffi ≥ 0.13.0

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/naver-dict-api.git
cd naver-dict-api

# Install dependencies with uv
uv sync

# Install in development mode
uv pip install -e .
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=naver_dict_api

# Run only unit tests (skip integration tests)
uv run pytest -m "not integration"
```

### Building

```bash
# Build distribution packages
uv build
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

This library uses the Naver Dictionary autocomplete API and is not officially affiliated with Naver Corporation.
