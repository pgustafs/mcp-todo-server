# MCP Todo Server

A Model Context Protocol (MCP) server that provides persistent todo list functionality for AI assistants. Built with Python and JSON file-based storage.

## 🌟 Features

- **Complete Todo Management**: Add, list, update, complete, and delete todos
- **Priority System**: Organize todos with low, medium, and high priority levels
- **Persistent Storage**: JSON file-based storage that survives server restarts
- **Rich Filtering**: Filter todos by completion status and priority
- **MCP Compatible**: Works with Claude Desktop, Open WebUI, and other MCP clients
- **Async Support**: Built with modern Python async/await patterns

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/pgustafs/mcp-todo-server.git
   cd mcp-todo-server
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate 
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

**Run the server directly:**
```bash
python src/todo_server.py
```

**With MCPO for remote access:**
```bash
mcpo --port 8000 --api-key "your-secret-key" -- python src/todo_server.py
```

## Container Deployment

### Building the Container

**Build with Podman:**
```bash
# Build the container image
podman build -t mcp-todo-server .

# Build with custom tag
podman build -t mcp-todo-server:v1.0.0 .
```

### Running the Container

**Run without persistent storage (temporary todos):**
```bash
# Basic run - todos will be lost when container stops
podman run -d \
  --name mcp-todo \
  -p 8000:8000 \
  mcp-todo-server

# With custom API key
podman run -d \
  --name mcp-todo \
  -p 8000:8000 \
  --env MCPO_API_KEY=my-secret-key \
  mcp-todo-server
```

**Run with persistent storage (recommended for production):**
```bash
# Create a volume for persistent storage
podman volume create todo-data

# Run with persistent volume
podman run -d \
  --name mcp-todo \
  -p 8000:8000 \
  -v todo-data:/opt/app-root/src/data \
  mcp-todo-server

# Alternative: Bind mount to host directory
mkdir -p ./todo-data
podman run -d \
  --name mcp-todo \
  -p 8000:8000 \
  -v ./todo-data:/opt/app-root/src/data:Z \
  mcp-todo-server
```

**Run with custom configuration:**
```bash
# Custom API key and storage path
podman run -d \
  --name mcp-todo \
  -p 8000:8000 \
  -v todo-data:/app/data \
  -e MCPO_API_KEY=my-super-secret-key \
  -e TODO_STORAGE_PATH=/app/data/my-todos.json \
  --restart=unless-stopped \
  mcp-todo-server
```

### Container Management

**View container logs:**
```bash
podman logs mcp-todo
podman logs -f mcp-todo  # Follow logs
```

**Stop and remove container:**
```bash
podman stop mcp-todo
podman rm mcp-todo
```

**Access container shell (for debugging):**
```bash
podman exec -it mcp-todo /bin/bash
```

**Container health check:**
```bash
podman healthcheck run mcp-todo
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCPO_API_KEY` | `top-secret` | API key for MCPO authentication |
| `TODO_STORAGE_PATH` | `/opt/app-root/src/data/todos.json` | Path to store the todos JSON file |
| `PYTHONPATH` | `/app` | Python module search path |
| `PYTHONUNBUFFERED` | `1` | Ensure Python output is not buffered |

### Container Security

The container runs as a non-root user (`appuser`, UID 1001) for enhanced security. The application data is stored in `/opt/app-root/src/data/` which should be mounted as a volume for persistence.

**SELinux considerations (for RHEL/Fedora hosts):**
```bash
# Use :Z flag for proper SELinux labeling
podman run -v ./todo-data:/app/data:Z mcp-todo-server
```

### Production Deployment

**Using systemd service:**
```bash
# Generate systemd service file
podman generate systemd --new --name mcp-todo > ~/.config/systemd/user/mcp-todo.service

# Enable and start service
systemctl --user daemon-reload
systemctl --user enable mcp-todo.service
systemctl --user start mcp-todo.service
```

**Container orchestration with podman play kube:**
```yaml
# mcp-todo-server-pod.yml
```

## 📋 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_todo` | Add a new todo item | `title` (required), `description`, `priority` |
| `list_todos` | List all todos with optional filtering | `completed` (boolean), `priority` (low/medium/high) |
| `get_todo` | Get specific todo by ID | `id` (required) |
| `update_todo` | Update an existing todo | `id` (required), `title`, `description`, `priority` |
| `complete_todo` | Mark todo as completed | `id` (required) |
| `uncomplete_todo` | Mark todo as not completed | `id` (required) |
| `delete_todo` | Delete a todo | `id` (required) |

## 🧪 Testing

### Run Test Suite

```bash
# Run all tests
python tests/test_todo_server.py
# Choose option 4 for comprehensive testing

# Run specific test categories
python tests/test_todo_server.py
# Option 1: Storage layer tests
# Option 2: MCP functionality tests  
# Option 3: Interactive testing
```

### Manual Testing

```bash
# Test with simple MCP client
python tests/simple_mcp_client.py
```

## 📱 Usage Examples

### Getting Started
```
"Help me manage my todos. Can you show me what's available?"
"What todos do I have right now?"
```

### Adding Todos
```
"Add a todo to call mom"
"Create a high priority todo to 'Finish quarterly report' with description 'Include Q3 metrics and projections for Q4'"
"Add these todos: Buy groceries (medium priority), Schedule dentist appointment (low priority)"
```

### Managing Todos
```
"Show me only my high priority todos"
"List all my completed todos"
"Mark todo #1 as completed"
"Change todo #2 to high priority"
"Delete todo #5, it's no longer relevant"
```

### Smart Workflow
```
"Analyze my todo list and tell me which high priority items I should focus on today"
"Give me a summary of my productivity - how many todos have I completed vs pending?"
"I have 30 minutes free. What low priority items could I knock out quickly?"
```

## 🔧 Configuration

### Claude Desktop Integration

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "todo-server": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-todo-server/src/todo_server.py"]
    }
  }
}
```

### Open WebUI Integration

1. **Install MCPO:**
   ```bash
   pip install mcpo
   ```

2. **Run with MCPO:**
   ```bash
   mcpo --port 8000 --api-key "your-secret-key" -- python src/todo_server.py
   ```

3. **Configure Open WebUI:**
   - Add MCP server URL: `http://localhost:8000`
   - Use your API key for authentication

### VS Code Integration

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "todo-server": {
      "type": "stdio",
      "command": "python",
      "args": ["src/todo_server.py"]
    }
  }
}
```

## 🏗️ Architecture

### Components

- **TodoItem**: Data model for individual todos
- **TodoStorage**: Handles JSON file persistence and CRUD operations
- **MCP Server**: Exposes tools via Model Context Protocol
- **Tool Handlers**: Process MCP tool calls and return formatted responses

### Data Storage

Todos are stored in `todos.json` with the following structure:

```json
{
  "todos": [
    {
      "id": 1,
      "title": "Example Todo",
      "description": "This is an example",
      "completed": false,
      "created_at": "2024-01-01T12:00:00",
      "completed_at": null,
      "priority": "medium"
    }
  ],
  "next_id": 2
}
```

## 🔍 API Reference

### Tool Schemas

<details>
<summary>add_todo</summary>

```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The title of the todo item"
    },
    "description": {
      "type": "string", 
      "description": "Optional description of the todo item"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high"],
      "description": "Priority level of the todo item"
    }
  },
  "required": ["title"]
}
```
</details>

<details>
<summary>list_todos</summary>

```json
{
  "type": "object",
  "properties": {
    "completed": {
      "type": "boolean",
      "description": "Filter by completion status"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high"],
      "description": "Filter by priority level"
    }
  }
}
```
</details>

## 🛠️ Development

### Requirements

- Python 3.9+
- MCP Python SDK 1.9.2+

### Project Structure

```
mcp-todo-server/
├── src/
│   └── todo_server.py          # Main server implementation
├── tests/
│   ├── test_todo_server.py     # Comprehensive test suite
│   └── simple_mcp_client.py    # Simple MCP client for testing
├── docs/
│   └── examples.md             # Additional usage examples
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Container orchestration
├── .dockerignore              # Docker build exclusions
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Running Tests

```bash
# Run storage tests
python tests/test_todo_server.py  # Choose option 1

# Run MCP integration tests  
python tests/test_todo_server.py  # Choose option 2

# Run interactive tests
python tests/test_todo_server.py  # Choose option 3

# Run all automated tests
python tests/test_todo_server.py  # Choose option 4
```

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
- Check Python version (3.9+ required)
- Verify MCP library installation: `pip install mcp>=1.9.2`
- Check file permissions for `todos.json`

**Tools not appearing in client:**
- Verify MCP client configuration
- Check server logs for initialization errors
- Ensure proper tool registration

**Persistence issues:**
- Check write permissions in server directory
- Verify `todos.json` file format
- Look for JSON parsing errors in logs

### Debug Mode

Run with debug output:
```bash
python -u src/todo_server.py
```

### Logging

The server outputs helpful information about:
- Todo storage operations
- MCP tool calls
- Error conditions

## 📚 Related Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/en/docs/build-with-claude/mcp)
- [Open WebUI MCP Integration](https://github.com/open-webui/mcpo)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- Built using the [Model Context Protocol](https://modelcontextprotocol.io/)
- Powered by the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Compatible with [Open WebUI](https://github.com/open-webui/open-webui) via [MCPO](https://github.com/open-webui/mcpo)

## 📈 Changelog

### v1.0.0
- Initial release with full todo management functionality
- MCP 1.9.2 compatibility
- JSON file-based persistence
- Comprehensive test suite
- Claude Desktop and Open WebUI integration support

---

**Built with ❤️  for fun**
