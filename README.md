# LLM Proxy Server

A Python application for proxying requests from VS Code extensions, such as Cline, Roo-Code, to various LLMs via API (Anthropic, DeepSeek, Moonshot, OpenRouter, xAI) with an OpenAI-compatible interface. Supports a GUI interface, usage statistics, logging, and localizations in 10 languages.

## Application Architecture

### Core Components

#### Application Core

- **`main.py`** - Entry point for launching the GUI interface
- **`server.py`** - Main FastAPI server with proxying logic
- **`gui.py`** - Graphical interface using tkinter with localization support
- **`config.py`** - Settings management via JSON configuration

#### LLM Providers

Located in the `providers/` directory:

- **`anthropic.py`** - Integration with Anthropic Claude
- **`deepseek.py`** - Integration with DeepSeek
- **`moonshot.py`** - Integration with Moonshot
- **`openrouter.py`** - Integration with OpenRouter
- **`xai.py`** - Integration with xAI Grok
- **`local.py`** - Local provider (for testing)

#### Utilities

- **`utils/token_counter.py`** - Token counting and request cost calculation

#### Configuration

- **`settings.json`** - Automatically created settings file
- **`requirements.txt`** - Python dependencies

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python main.py
```

## Provider Configuration

Open the GUI and go to settings (⚙ button). For each provider:

1. Enable the provider (checkbox "Enabled")
2. Specify the API key
3. Select a model from the available list

### Supported Providers

| Provider   | Models                           | Features                        |
| ---------- | -------------------------------- | ------------------------------- |
| Anthropic  | Claude 3.5 Sonnet, Claude 3 Opus | High quality, reasoning support |
| DeepSeek   | DeepSeek Chat, DeepSeek Coder    | Economical, good performance    |
| Moonshot   | Kimi k2                          | Chinese provider                |
| OpenRouter | 100+ models                      | Universal access to all models  |
| xAI        | Grok                             | Model from xAI                  |
| Local      | GPT-OSS-120B                     | Local model for testing         |

## Usage

### GUI Mode (Recommended)

1. Run `python main.py`
2. Select a provider from the dropdown list
3. Click "▶ Start" to start the server
4. Server will be available at `http://localhost:8000`

### Server Mode

```bash
python server.py
# or
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Alternative Launch

```bash
python run_server.py
```

## Localizations

The application supports 10 interface languages:

- English (en)
- Русский (ru)
- 中文 (zh)
- Español (es)
- हिन्दी (hi)
- العربية (ar)
- বাংলা (bn)
- Português (pt)
- 日本語 (ja)
- Deutsch (de)

Language is selected in the GUI settings.

## Statistics and Logging

### Usage Statistics

- Number of processed requests
- Total token count (input + output)
- Cost calculation for paid providers

### Logging

- Request and response logs in GUI
- Optional log saving to file
- Display of last 100 requests/responses

## API Endpoints

### Main Endpoints

- `GET /` - Server status
- `GET /health` - Health check
- `POST /v1/chat/completions` - Main chat endpoint
- `GET /stats` - Server statistics
- `GET /logs/requests` - Request logs
- `GET /logs/responses` - Response logs
- `GET /logs/all` - All logs

### Provider Management

- `GET /providers` - List of available providers
- `POST /switch-provider/{provider_name}` - Switch provider

### Debugging

- `POST /debug/cline` - Debug requests from Cline

## Compatibility with IDE Extensions

### VS Code + Cline

1. Install the Cline or Roo-Code extension for VS Code
2. In settings specify:
   - **API Provider:** OpenAI Compatible
   - **Base URL:** `http://localhost:8000/v1` (or PC IP in local/external network, e.g., http://192.168.1.44:8000/v1)
   - **API Key:** any non-empty key (ignored by proxy)
   - **Model:** any model from the list (ignored by proxy)

### Other Extensions

For extensions with OpenAI API support:

- **Base URL:** `http://localhost:8000` or `http://localhost:8000/v1`
- **API Key:** any key (not used)

## Features

- **Streaming Support:** Full streaming response support
- **Multimodality:** Support for images and complex content
- **Flexible Configuration:** Easy addition of new providers
- **Statistics:** Detailed usage and cost tracking
- **Localizations:** Support for 10 interface languages
- **Compatibility:** OpenAI-compatible API for maximum compatibility

## Development

To add a new provider:

1. Create a file in `providers/`
2. Implement a class with `chat_completion()` method
3. Add the provider to `server.py`
4. Update settings in `config.py` and `settings.xml`

## File Structure

```
proxy_llm/
├── main.py              # GUI entry point
├── server.py            # FastAPI server
├── gui.py               # Graphical interface
├── config.py            # Settings management
├── run_server.py       # Alternative server launch
├── requirements.txt     # Dependencies
├── settings.json        # Settings (created automatically)
├── providers/           # Provider modules
│   ├── anthropic.py
│   ├── deepseek.py
│   ├── moonshot.py
│   ├── openrouter.py
│   ├── xai.py
│   └── local.py
├── utils/               # Utilities
│   └── token_counter.py
└── logs/                # Logs directory (created automatically)
```

## License

MIT License
