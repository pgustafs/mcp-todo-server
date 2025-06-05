#!/usr/bin/env python3
"""
Todo MCP Server with Persistent Storage

A Model Context Protocol server that provides todo list functionality
with JSON file-based persistence.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
import mcp.server.stdio


# Data Models
@dataclass
class TodoItem:
    """Represents a single todo item"""
    id: int
    title: str
    description: str = ""
    completed: bool = False
    created_at: str = ""
    completed_at: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def complete(self):
        """Mark the todo item as completed"""
        self.completed = True
        self.completed_at = datetime.now().isoformat()
    
    def uncomplete(self):
        """Mark the todo item as not completed"""
        self.completed = False
        self.completed_at = None


class TodoStorage:
    """Handles persistent storage of todo items using JSON files"""
    
    def __init__(self, storage_path: Optional[str] = None):
        # Use environment variable if available, otherwise default
        if storage_path is None:
            storage_path = os.getenv('TODO_STORAGE_PATH', 'todos.json')
        
        self.storage_path = Path(storage_path)
        
        # Ensure the directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.todos: List[TodoItem] = []
        self._next_id = 1
        self.load()
    
    def load(self):
        """Load todos from JSON file"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.todos = [TodoItem(**item) for item in data.get('todos', [])]
                    self._next_id = data.get('next_id', 1)
            else:
                self.todos = []
                self._next_id = 1
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading todos: {e}")
            self.todos = []
            self._next_id = 1
    
    def save(self):
        """Save todos to JSON file"""
        try:
            data = {
                'todos': [asdict(todo) for todo in self.todos],
                'next_id': self._next_id
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving todos: {e}")
    
    def add_todo(self, title: str, description: str = "", priority: str = "medium") -> TodoItem:
        """Add a new todo item"""
        todo = TodoItem(
            id=self._next_id,
            title=title,
            description=description,
            priority=priority
        )
        self.todos.append(todo)
        self._next_id += 1
        self.save()
        return todo
    
    def get_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Get a todo item by ID"""
        return next((todo for todo in self.todos if todo.id == todo_id), None)
    
    def get_all_todos(self) -> List[TodoItem]:
        """Get all todo items"""
        return self.todos.copy()
    
    def update_todo(self, todo_id: int, **kwargs) -> Optional[TodoItem]:
        """Update a todo item"""
        todo = self.get_todo(todo_id)
        if todo:
            for key, value in kwargs.items():
                if hasattr(todo, key):
                    setattr(todo, key, value)
            self.save()
        return todo
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item"""
        todo = self.get_todo(todo_id)
        if todo:
            self.todos.remove(todo)
            self.save()
            return True
        return False
    
    def complete_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Mark a todo as completed"""
        todo = self.get_todo(todo_id)
        if todo:
            todo.complete()
            self.save()
        return todo
    
    def uncomplete_todo(self, todo_id: int) -> Optional[TodoItem]:
        """Mark a todo as not completed"""
        todo = self.get_todo(todo_id)
        if todo:
            todo.uncomplete()
            self.save()
        return todo


# Initialize storage
storage = TodoStorage()

# Create the MCP server
server = Server("todo-server")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools for the todo server"""
    return [
        types.Tool(
            name="add_todo",
            description="Add a new todo item",
            inputSchema={
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
        ),
        types.Tool(
            name="list_todos",
            description="List all todo items with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "completed": {
                        "type": "boolean",
                        "description": "Filter by completion status (true/false)"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Filter by priority level"
                    }
                }
            }
        ),
        types.Tool(
            name="get_todo",
            description="Get a specific todo item by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the todo item"
                    }
                },
                "required": ["id"]
            }
        ),
        types.Tool(
            name="update_todo",
            description="Update a todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the todo item"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title for the todo item"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the todo item"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority level"
                    }
                },
                "required": ["id"]
            }
        ),
        types.Tool(
            name="complete_todo",
            description="Mark a todo item as completed",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the todo item to complete"
                    }
                },
                "required": ["id"]
            }
        ),
        types.Tool(
            name="uncomplete_todo",
            description="Mark a todo item as not completed",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the todo item to uncomplete"
                    }
                },
                "required": ["id"]
            }
        ),
        types.Tool(
            name="delete_todo",
            description="Delete a todo item",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the todo item to delete"
                    }
                },
                "required": ["id"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls from the client"""
    
    if name == "add_todo":
        title = arguments["title"]
        description = arguments.get("description", "")
        priority = arguments.get("priority", "medium")
        
        todo = storage.add_todo(title, description, priority)
        return [types.TextContent(
            type="text",
            text=f"Added todo item #{todo.id}: {todo.title}"
        )]
    
    elif name == "list_todos":
        todos = storage.get_all_todos()
        
        # Apply filters
        if "completed" in arguments:
            todos = [t for t in todos if t.completed == arguments["completed"]]
        if "priority" in arguments:
            todos = [t for t in todos if t.priority == arguments["priority"]]
        
        if not todos:
            return [types.TextContent(type="text", text="No todos found")]
        
        # Format the todo list
        todo_list = []
        for todo in todos:
            status = "✓" if todo.completed else "○"
            priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴"}[todo.priority]
            todo_list.append(f"{status} #{todo.id} {priority_emoji} {todo.title}")
            if todo.description:
                todo_list.append(f"    {todo.description}")
        
        return [types.TextContent(
            type="text",
            text="Todo List:\n" + "\n".join(todo_list)
        )]
    
    elif name == "get_todo":
        todo_id = arguments["id"]
        todo = storage.get_todo(todo_id)
        
        if not todo:
            return [types.TextContent(
                type="text",
                text=f"Todo item #{todo_id} not found"
            )]
        
        status = "Completed" if todo.completed else "Pending"
        priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴"}[todo.priority]
        
        details = [
            f"Todo #{todo.id}",
            f"Title: {todo.title}",
            f"Description: {todo.description or 'None'}",
            f"Status: {status}",
            f"Priority: {priority_emoji} {todo.priority.title()}",
            f"Created: {todo.created_at}"
        ]
        
        if todo.completed_at:
            details.append(f"Completed: {todo.completed_at}")
        
        return [types.TextContent(
            type="text",
            text="\n".join(details)
        )]
    
    elif name == "update_todo":
        todo_id = arguments["id"]
        updates = {k: v for k, v in arguments.items() if k != "id"}
        
        todo = storage.update_todo(todo_id, **updates)
        if not todo:
            return [types.TextContent(
                type="text",
                text=f"Todo item #{todo_id} not found"
            )]
        
        return [types.TextContent(
            type="text",
            text=f"Updated todo item #{todo.id}: {todo.title}"
        )]
    
    elif name == "complete_todo":
        todo_id = arguments["id"]
        todo = storage.complete_todo(todo_id)
        
        if not todo:
            return [types.TextContent(
                type="text",
                text=f"Todo item #{todo_id} not found"
            )]
        
        return [types.TextContent(
            type="text",
            text=f"Completed todo item #{todo.id}: {todo.title}"
        )]
    
    elif name == "uncomplete_todo":
        todo_id = arguments["id"]
        todo = storage.uncomplete_todo(todo_id)
        
        if not todo:
            return [types.TextContent(
                type="text",
                text=f"Todo item #{todo_id} not found"
            )]
        
        return [types.TextContent(
            type="text",
            text=f"Uncompleted todo item #{todo.id}: {todo.title}"
        )]
    
    elif name == "delete_todo":
        todo_id = arguments["id"]
        success = storage.delete_todo(todo_id)
        
        if not success:
            return [types.TextContent(
                type="text",
                text=f"Todo item #{todo_id} not found"
            )]
        
        return [types.TextContent(
            type="text",
            text=f"Deleted todo item #{todo_id}"
        )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Main entry point for the server"""
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # Create proper notification options for MCP 1.9.2
        notification_options = NotificationOptions()
        experimental_capabilities = {}
        
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="todo-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=notification_options,
                    experimental_capabilities=experimental_capabilities
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
