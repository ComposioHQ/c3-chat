# C3 Chat Application

A Chainlit-based chat application that integrates with GitHub through Composio and uses Anthropic's Claude for chat functionality.

## Features

- Chat with Claude AI model
- GitHub integration through Composio
- User authentication (OAuth and password-based)
- Tool usage with Claude

## Project Structure

The project follows a modular structure:

```
├── src/
│   ├── api/            # API client modules
│   │   ├── claude.py   # Claude API client
│   │   └── composio.py # Composio integration
│   └── controllers/    # Request controllers
│       ├── actions.py  # Action controllers 
│       └── chat.py     # Chat controllers
├── main.py             # Main application
├── config.py           # Configuration settings
├── callbacks.py        # Authentication callbacks
├── prompts.py          # System prompts
├── run.py              # Runner script
└── .env                # Environment variables
```

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -e .
   ```
4. Set up the environment variables in `.env`:
   ```
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   RAILWAY_PUBLIC_DOMAIN=your_railway_domain
   ```

## Running the Application

You can run the application using one of the following methods:

### Using the provided script

The script automatically includes the watch mode and host flags:

```bash
./run.py
```

### Using the Chainlit CLI directly

With watch mode and host flags (recommended):

```bash
chainlit run main.py -w -h
```

Without flags:

```bash
chainlit run main.py
```

## Configuration

The application can be configured using environment variables. See `config.py` for details.

## Development

To add new features or integrations:

1. Create a new module in the appropriate directory
2. Register any callbacks in `main.py`
3. Update the configuration if necessary
