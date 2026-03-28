# Telegram MCP Server

A full-featured Telegram integration for Claude, Cursor, and other MCP-compatible clients. Uses [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram API access and exposes 60+ tools via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Features

- **60+ Telegram Tools**: Messaging, contacts, groups, channels, reactions, media, and more
- **Flexible ID Support**: Accept integer IDs, string IDs, or `@username` formats
- **Session Options**: Supports both string-based and file-based Telegram sessions
- **MCP Compatible**: Works with Claude Desktop, Cursor, and any MCP client
- **TypeScript Agent**: Optional CLI agent powered by Claude Sonnet

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   MCP Client     │────▶│   MCP Server     │────▶│    Telegram      │
│ (Claude/Cursor)  │     │   (main.py)      │     │    Servers       │
└──────────────────┘     └──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   CLI Agent      │────▶│  Telegram API    │────▶│    Telegram      │
│  (TypeScript)    │     │   Bridge (Py)    │     │    Servers       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

## Quick Start

### 1. Get Telegram API Credentials

Get your API credentials at [my.telegram.org/apps](https://my.telegram.org/apps).

### 2. Install & Configure

```bash
# Clone the repo
git clone https://github.com/jamolovmn/desktop-tutorial.git
cd telegram-mcp

# Install Python dependencies
uv sync

# Generate Telegram session string
uv run session_string_generator.py

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 3. Use as MCP Server (Recommended)

Add to your MCP config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "uv",
      "args": ["--directory", "/path/to/desktop-tutorial", "run", "main.py"]
    }
  }
}
```

Or run directly:

```bash
uv run main.py
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Telegram API (Required)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Session (choose one)
TELEGRAM_SESSION_STRING=your_session_string   # preferred
TELEGRAM_SESSION_NAME=your_session_name       # file-based alternative
```

For the TypeScript agent, also add:

```env
AI_GATEWAY_API_KEY=your_vercel_ai_gateway_key
NIA_API_KEY=your_nia_api_key
TELEGRAM_API_URL=http://localhost:8765
```

## Available MCP Tools (60+)

**Messaging**
| Tool | Description |
|------|-------------|
| `send_message` | Send a message to a chat |
| `reply_to_message` | Reply to a specific message |
| `edit_message` | Edit a sent message |
| `delete_message` | Delete a message |
| `forward_message` | Forward a message to another chat |
| `pin_message` | Pin a message in a chat |
| `send_reaction` | React to a message with an emoji |

**Chats & Channels**
| Tool | Description |
|------|-------------|
| `get_chats` | List all conversations |
| `get_messages` | Read messages from a chat |
| `search_messages` | Search messages by text |
| `get_history` | Get message history (up to 500) |
| `mark_as_read` | Mark messages as read |

**Contacts**
| Tool | Description |
|------|-------------|
| `search_contacts` | Search your contacts |
| `get_user_status` | Check if a user is online |
| `get_user_photos` | Get a user's profile photos |

**Group & Channel Management**
| Tool | Description |
|------|-------------|
| `create_group` | Create a new group |
| `invite_to_group` | Invite users to a group |
| `set_admin` | Grant admin rights |
| `ban_user` | Ban a user from a group |

**Media**
| Tool | Description |
|------|-------------|
| `send_file` | Send a file or media |
| `download_media` | Download media from a message |
| `search_gifs` | Search for GIFs |

Full list of tools available in `main.py`.

## Optional: TypeScript CLI Agent

A CLI agent using Claude Sonnet is available in the `agent/` directory. It communicates with Telegram via an HTTP bridge.

```bash
# Start the API bridge
python telegram_api.py

# In a new terminal, run the agent
cd agent
bun install
bun run dev
```

## Docker

```bash
docker build -t telegram-mcp:latest .
docker compose up --build
```

## Development

```bash
# Format code
black .

# Lint code
flake8 .

# Run tests
pytest test_validation.py -v
```

## Troubleshooting

- **Database lock errors**: Use session string auth instead of file-based
- **Auth errors**: Regenerate session string with `uv run session_string_generator.py`
- **Connection issues**: Check that `telegram_api.py` is running on port 8765
- **Error logs**: Check `mcp_errors.log` for detailed errors

## Security

- Never commit your `.env` file or session string
- A session string grants full access to your Telegram account — keep it safe
- All processing is local; data only goes to Telegram's API servers

## License

[Apache 2.0](LICENSE)
