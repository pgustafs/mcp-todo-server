#!/usr/bin/env python3
"""
Simple MCP Client for Testing Todo Server

This client connects to the todo server and allows you to test
the MCP protocol communication directly.
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List


class SimpleMCPClient:
    """A simple MCP client for testing purposes"""
    
    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.process = None
        self.request_id = 1
    
    async def start_server(self):
        """Start the MCP server process"""
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("✅ Server started")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server"""
        if not self.process:
            raise RuntimeError("Server not started")
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode().strip())
        
        self.request_id += 1
        return response
    
    async def initialize(self):
        """Initialize the MCP connection"""
        response = await self.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )
        print("✅ Initialized connection")
        return response
    
    async def list_tools(self):
        """List available tools"""
        response = await self.send_request("tools/list")
        print("📋 Available tools:")
        if "result" in response and "tools" in response["result"]:
            for tool in response["result"]["tools"]:
                print(f"  - {tool['name']}: {tool['description']}")
        return response
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        """Call a tool"""
        response = await self.send_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments
            }
        )
        
        if "result" in response:
            print(f"🔧 Tool '{name}' result:")
            for content in response["result"]["content"]:
                if content["type"] == "text":
                    print(content["text"])
        elif "error" in response:
            print(f"❌ Error calling '{name}': {response['error']}")
        
        return response
    
    async def stop_server(self):
        """Stop the server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("✅ Server stopped")


async def run_comprehensive_test():
    """Run a comprehensive test of the MCP server"""
    client = SimpleMCPClient([sys.executable, "src/todo_server.py"])
    
    try:
        # Start server and initialize
        await client.start_server()
        await client.initialize()
        
        # List available tools
        await client.list_tools()
        
        print("\n" + "="*50)
        print("🧪 Running Comprehensive Tests")
        print("="*50)
        
        # Test 1: Add todos
        print("\n1️⃣ Adding todos...")
        await client.call_tool("add_todo", {
            "title": "Learn MCP Protocol",
            "description": "Study the Model Context Protocol documentation",
            "priority": "high"
        })
        
        await client.call_tool("add_todo", {
            "title": "Write unit tests",
            "description": "Create comprehensive test suite",
            "priority": "medium"
        })
        
        await client.call_tool("add_todo", {
            "title": "Deploy to production",
            "priority": "low"
        })
        
        # Test 2: List all todos
        print("\n2️⃣ Listing all todos...")
        await client.call_tool("list_todos", {})
        
        # Test 3: Get specific todo
        print("\n3️⃣ Getting specific todo...")
        await client.call_tool("get_todo", {"id": 1})
        
        # Test 4: Complete a todo
        print("\n4️⃣ Completing todo...")
        await client.call_tool("complete_todo", {"id": 1})
        
        # Test 5: List completed todos
        print("\n5️⃣ Listing completed todos...")
        await client.call_tool("list_todos", {"completed": True})
        
        # Test 6: Update a todo
        print("\n6️⃣ Updating todo...")
        await client.call_tool("update_todo", {
            "id": 2,
            "title": "Write comprehensive unit tests",
            "priority": "high"
        })
        
        # Test 7: List high priority todos
        print("\n7️⃣ Listing high priority todos...")
        await client.call_tool("list_todos", {"priority": "high"})
        
        # Test 8: Delete a todo
        print("\n8️⃣ Deleting todo...")
        await client.call_tool("delete_todo", {"id": 3})
        
        # Test 9: Final list
        print("\n9️⃣ Final todo list...")
        await client.call_tool("list_todos", {})
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.stop_server()


async def interactive_client():
    """Interactive MCP client for manual testing"""
    client = SimpleMCPClient([sys.executable, "src/todo_server.py"])
    
    try:
        await client.start_server()
        await client.initialize()
        await client.list_tools()
        
        print("\n🎮 Interactive MCP Client")
        print("Type 'help' for commands, 'quit' to exit")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if command == "quit":
                    break
                elif command == "help":
                    print("Available commands:")
                    print("  add <title> [description] [priority]")
                    print("  list [completed=true/false] [priority=low/medium/high]")
                    print("  get <id>")
                    print("  complete <id>")
                    print("  uncomplete <id>")
                    print("  update <id> [title] [description] [priority]")
                    print("  delete <id>")
                    print("  tools")
                    print("  quit")
                
                elif command.startswith("add "):
                    parts = command[4:].split()
                    if len(parts) >= 1:
                        args = {"title": parts[0]}
                        if len(parts) >= 2:
                            args["description"] = parts[1]
                        if len(parts) >= 3:
                            args["priority"] = parts[2]
                        await client.call_tool("add_todo", args)
                
                elif command.startswith("list"):
                    args = {}
                    if "completed=true" in command:
                        args["completed"] = True
                    elif "completed=false" in command:
                        args["completed"] = False
                    if "priority=" in command:
                        for priority in ["low", "medium", "high"]:
                            if f"priority={priority}" in command:
                                args["priority"] = priority
                    await client.call_tool("list_todos", args)
                
                elif command.startswith("get "):
                    todo_id = int(command[4:])
                    await client.call_tool("get_todo", {"id": todo_id})
                
                elif command.startswith("complete "):
                    todo_id = int(command[9:])
                    await client.call_tool("complete_todo", {"id": todo_id})
                
                elif command.startswith("uncomplete "):
                    todo_id = int(command[11:])
                    await client.call_tool("uncomplete_todo", {"id": todo_id})
                
                elif command.startswith("delete "):
                    todo_id = int(command[7:])
                    await client.call_tool("delete_todo", {"id": todo_id})
                
                elif command == "tools":
                    await client.list_tools()
                
                else:
                    print("Unknown command. Type 'help' for available commands.")
            
            except (ValueError, IndexError):
                print("Invalid command format. Type 'help' for usage.")
            except KeyboardInterrupt:
                break
    
    except Exception as e:
        print(f"❌ Client error: {e}")
    
    finally:
        await client.stop_server()


def main():
    """Main entry point"""
    print("🧪 MCP Todo Server Testing Client")
    print("Choose testing mode:")
    print("1. Comprehensive automated test")
    print("2. Interactive client")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        asyncio.run(run_comprehensive_test())
    elif choice == "2":
        asyncio.run(interactive_client())
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
