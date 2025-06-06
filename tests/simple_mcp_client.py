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
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("✅ Server started")
            
            # Give the server a moment to initialize
            await asyncio.sleep(1)
            
            # Check if process is still running
            if self.process.returncode is not None:
                stderr_output = await self.process.stderr.read()
                print(f"❌ Server failed to start: {stderr_output.decode()}")
                return False
            
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
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
        
        try:
            # Send request
            request_line = json.dumps(request) + "\n"
            self.process.stdin.write(request_line.encode())
            await self.process.stdin.drain()
            
            # Read response with timeout
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(), 
                timeout=5.0
            )
            
            if not response_line:
                raise RuntimeError("Server closed connection")
                
            response = json.loads(response_line.decode().strip())
            self.request_id += 1
            return response
            
        except asyncio.TimeoutError:
            print(f"❌ Timeout waiting for response to {method}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"Raw response: {response_line}")
            raise
        except Exception as e:
            print(f"❌ Error sending request {method}: {e}")
            raise
    
    async def initialize(self):
        """Initialize the MCP connection"""
        try:
            response = await asyncio.wait_for(
                self.send_request(
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
                ),
                timeout=10.0
            )
            print("✅ Initialized connection")
            return response
        except asyncio.TimeoutError:
            print("❌ Initialization timeout - server may not be responding properly")
            return None
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return None
    
    async def list_tools(self):
        """List available tools"""
        try:
            response = await asyncio.wait_for(
                self.send_request("tools/list"),
                timeout=10.0
            )
            print("📋 Available tools:")
            if "result" in response and "tools" in response["result"]:
                for tool in response["result"]["tools"]:
                    print(f"  - {tool['name']}: {tool['description']}")
            elif "error" in response:
                print(f"❌ Error: {response['error']}")
            return response
        except asyncio.TimeoutError:
            print("❌ Timeout listing tools")
            return None
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return None
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        """Call a tool"""
        try:
            response = await asyncio.wait_for(
                self.send_request(
                    "tools/call",
                    {
                        "name": name,
                        "arguments": arguments
                    }
                ),
                timeout=10.0
            )
            
            if "result" in response:
                print(f"🔧 Tool '{name}' result:")
                for content in response["result"]["content"]:
                    if content["type"] == "text":
                        print(content["text"])
            elif "error" in response:
                print(f"❌ Error calling '{name}': {response['error']}")
            
            return response
        except asyncio.TimeoutError:
            print(f"❌ Timeout calling tool '{name}'")
            return None
        except Exception as e:
            print(f"❌ Error calling tool '{name}': {e}")
            return None
    
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
        if not await client.start_server():
            return
        
        init_result = await client.initialize()
        if init_result is None:
            print("❌ Failed to initialize connection")
            return
        
        # List available tools
        tools_result = await client.list_tools()
        if tools_result is None:
            print("❌ Failed to list tools")
            return
        
        print("\n" + "="*50)
        print("🧪 Running Comprehensive Tests")
        print("="*50)
        
        # Test 1: Add todos
        print("\n1️⃣ Adding todos...")
        result1 = await client.call_tool("add_todo", {
            "title": "Learn MCP Protocol",
            "description": "Study the Model Context Protocol documentation",
            "priority": "high"
        })
        
        result2 = await client.call_tool("add_todo", {
            "title": "Write unit tests",
            "description": "Create comprehensive test suite",
            "priority": "medium"
        })
        
        result3 = await client.call_tool("add_todo", {
            "title": "Deploy to production",
            "priority": "low"
        })
        
        if not all([result1, result2, result3]):
            print("❌ Failed to add todos")
            return
        
        # Test 2: List all todos
        print("\n2️⃣ Listing all todos...")
        list_result = await client.call_tool("list_todos", {})
        if not list_result:
            print("❌ Failed to list todos")
            return
        
        # Test 3: Get specific todo
        print("\n3️⃣ Getting specific todo...")
        get_result = await client.call_tool("get_todo", {"id": 1})
        if not get_result:
            print("❌ Failed to get todo")
            return
        
        # Test 4: Complete a todo
        print("\n4️⃣ Completing todo...")
        complete_result = await client.call_tool("complete_todo", {"id": 1})
        if not complete_result:
            print("❌ Failed to complete todo")
            return
        
        # Test 5: List completed todos
        print("\n5️⃣ Listing completed todos...")
        completed_list = await client.call_tool("list_todos", {"completed": True})
        if not completed_list:
            print("❌ Failed to list completed todos")
            return
        
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
        if not await client.start_server():
            return
        
        init_result = await client.initialize()
        if init_result is None:
            print("❌ Failed to initialize connection")
            return
        
        tools_result = await client.list_tools()
        if tools_result is None:
            print("❌ Failed to list tools")
            return
        
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
                    try:
                        todo_id = int(command[4:])
                        await client.call_tool("get_todo", {"id": todo_id})
                    except ValueError:
                        print("❌ Invalid ID format")
                
                elif command.startswith("complete "):
                    try:
                        todo_id = int(command[9:])
                        await client.call_tool("complete_todo", {"id": todo_id})
                    except ValueError:
                        print("❌ Invalid ID format")
                
                elif command.startswith("uncomplete "):
                    try:
                        todo_id = int(command[11:])
                        await client.call_tool("uncomplete_todo", {"id": todo_id})
                    except ValueError:
                        print("❌ Invalid ID format")
                
                elif command.startswith("delete "):
                    try:
                        todo_id = int(command[7:])
                        await client.call_tool("delete_todo", {"id": todo_id})
                    except ValueError:
                        print("❌ Invalid ID format")
                
                elif command == "tools":
                    await client.list_tools()
                
                else:
                    print("Unknown command. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"❌ Command error: {e}")
    
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
