#!/usr/bin/env python3
"""
Test suite for Todo MCP Server

This file contains various ways to test the MCP server:
1. Unit tests for the storage layer
2. MCP client simulator
3. Manual testing utilities
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
import sys
import os

# Add the current directory to path so we can import our server
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

# Import our server components
from todo_server import TodoItem, TodoStorage, server


class TestTodoStorage(unittest.TestCase):
    """Unit tests for the TodoStorage class"""
    
    def setUp(self):
        """Set up test environment with temporary file"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.storage = TodoStorage(self.temp_file.name)
    
    def tearDown(self):
        """Clean up temporary file"""
        os.unlink(self.temp_file.name)
    
    def test_add_todo(self):
        """Test adding a new todo"""
        todo = self.storage.add_todo("Test Todo", "Test Description", "high")
        
        self.assertEqual(todo.title, "Test Todo")
        self.assertEqual(todo.description, "Test Description")
        self.assertEqual(todo.priority, "high")
        self.assertEqual(todo.id, 1)
        self.assertFalse(todo.completed)
        self.assertIsNotNone(todo.created_at)
    
    def test_get_todo(self):
        """Test retrieving a todo by ID"""
        todo = self.storage.add_todo("Test Todo")
        retrieved = self.storage.get_todo(todo.id)
        
        self.assertEqual(retrieved.title, "Test Todo")
        self.assertEqual(retrieved.id, todo.id)
    
    def test_get_nonexistent_todo(self):
        """Test retrieving a non-existent todo"""
        result = self.storage.get_todo(999)
        self.assertIsNone(result)
    
    def test_complete_todo(self):
        """Test completing a todo"""
        todo = self.storage.add_todo("Test Todo")
        completed = self.storage.complete_todo(todo.id)
        
        self.assertTrue(completed.completed)
        self.assertIsNotNone(completed.completed_at)
    
    def test_uncomplete_todo(self):
        """Test uncompleting a todo"""
        todo = self.storage.add_todo("Test Todo")
        self.storage.complete_todo(todo.id)
        uncompleted = self.storage.uncomplete_todo(todo.id)
        
        self.assertFalse(uncompleted.completed)
        self.assertIsNone(uncompleted.completed_at)
    
    def test_update_todo(self):
        """Test updating a todo"""
        todo = self.storage.add_todo("Original Title")
        updated = self.storage.update_todo(todo.id, title="Updated Title", priority="high")
        
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.priority, "high")
    
    def test_delete_todo(self):
        """Test deleting a todo"""
        todo = self.storage.add_todo("Test Todo")
        success = self.storage.delete_todo(todo.id)
        
        self.assertTrue(success)
        self.assertIsNone(self.storage.get_todo(todo.id))
    
    def test_delete_nonexistent_todo(self):
        """Test deleting a non-existent todo"""
        success = self.storage.delete_todo(999)
        self.assertFalse(success)
    
    def test_persistence(self):
        """Test that todos persist across storage instances"""
        # Add todo with first storage instance
        self.storage.add_todo("Persistent Todo", "Should survive restart")
        
        # Create new storage instance with same file
        new_storage = TodoStorage(self.temp_file.name)
        
        # Verify todo exists
        todos = new_storage.get_all_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].title, "Persistent Todo")
    
    def test_auto_increment_ids(self):
        """Test that IDs auto-increment correctly"""
        todo1 = self.storage.add_todo("Todo 1")
        todo2 = self.storage.add_todo("Todo 2")
        todo3 = self.storage.add_todo("Todo 3")
        
        self.assertEqual(todo1.id, 1)
        self.assertEqual(todo2.id, 2)
        self.assertEqual(todo3.id, 3)


class TestMCPTools(unittest.TestCase):
    """Test MCP tool functionality directly"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        # Create a test storage for this test
        global storage
        from todo_server import TodoStorage
        storage = TodoStorage(self.temp_file.name)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_file.name)
    
    async def test_add_todo_tool(self):
        """Test the add_todo tool"""
        from todo_server import handle_call_tool
        
        result = await handle_call_tool(
            "add_todo", 
            {"title": "Test MCP Todo", "description": "Testing via MCP", "priority": "high"}
        )
        
        self.assertEqual(len(result), 1)
        self.assertIn("Added todo item #1: Test MCP Todo", result[0].text)
    
    async def test_list_todos_tool(self):
        """Test the list_todos tool"""
        from todo_server import handle_call_tool
        
        # Add a todo first
        await handle_call_tool("add_todo", {"title": "Test Todo"})
        
        # List todos
        result = await handle_call_tool("list_todos", {})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Test Todo", result[0].text)
        self.assertIn("Todo List:", result[0].text)
    
    async def test_get_todo_tool(self):
        """Test the get_todo tool"""
        from todo_server import handle_call_tool
        
        # Add a todo first
        await handle_call_tool("add_todo", {"title": "Test Todo", "description": "Test Description"})
        
        # Get the todo
        result = await handle_call_tool("get_todo", {"id": 1})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Todo #1", result[0].text)
        self.assertIn("Test Todo", result[0].text)
        self.assertIn("Test Description", result[0].text)


class TestMCPServer(unittest.TestCase):
    """Test MCP server functionality"""
    
    def test_server_creation(self):
        """Test that server can be created"""
        from todo_server import server
        self.assertEqual(server.name, "todo-server")
    
    async def test_list_tools(self):
        """Test that tools are properly listed"""
        from todo_server import handle_list_tools
        
        tools = await handle_list_tools()
        
        # Check that all expected tools are present
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "add_todo", "list_todos", "get_todo", "update_todo",
            "complete_todo", "uncomplete_todo", "delete_todo"
        ]
        
        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names)
    
    def test_notification_options_import(self):
        """Test that NotificationOptions can be imported correctly"""
        try:
            from mcp.server.lowlevel import NotificationOptions
            notification_options = NotificationOptions()
            self.assertIsNotNone(notification_options)
        except ImportError:
            self.fail("Failed to import NotificationOptions from mcp.server.lowlevel")


class MCPAsyncTestCase(unittest.TestCase):
    """Base class for running async tests"""
    
    def run_async_test(self, coro):
        """Helper to run async tests"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class TestMCPToolsAsync(MCPAsyncTestCase):
    """Async tests for MCP tools"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        # Reset storage for each test
        global storage
        from todo_server import TodoStorage
        storage = TodoStorage(self.temp_file.name)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_file.name)
    
    def test_complete_workflow_async(self):
        """Test complete workflow asynchronously"""
        async def test():
            from todo_server import handle_call_tool
            
            # Add todo
            result1 = await handle_call_tool(
                "add_todo", 
                {"title": "Workflow Test", "priority": "high"}
            )
            self.assertIn("Added todo item #1", result1[0].text)
            
            # List todos
            result2 = await handle_call_tool("list_todos", {})
            self.assertIn("Workflow Test", result2[0].text)
            
            # Complete todo
            result3 = await handle_call_tool("complete_todo", {"id": 1})
            self.assertIn("Completed todo item #1", result3[0].text)
            
            # List completed todos
            result4 = await handle_call_tool("list_todos", {"completed": True})
            self.assertIn("Workflow Test", result4[0].text)
        
        self.run_async_test(test())


class InteractiveTestRunner:
    """Interactive testing utility"""
    
    def __init__(self):
        self.storage = TodoStorage("test_todos.json")
    
    def run_interactive_test(self):
        """Run interactive testing session"""
        print("Interactive Todo MCP Server Test")
        print("=" * 40)
        
        while True:
            print("\nChoose a test:")
            print("1. Add todo")
            print("2. List todos")
            print("3. Complete todo")
            print("4. Get todo details")
            print("5. Update todo")
            print("6. Delete todo")
            print("7. Test persistence")
            print("8. Test MCP tools directly")
            print("9. Exit")
            
            choice = input("\nEnter choice (1-9): ").strip()
            
            if choice == "1":
                self._test_add_todo()
            elif choice == "2":
                self._test_list_todos()
            elif choice == "3":
                self._test_complete_todo()
            elif choice == "4":
                self._test_get_todo()
            elif choice == "5":
                self._test_update_todo()
            elif choice == "6":
                self._test_delete_todo()
            elif choice == "7":
                self._test_persistence()
            elif choice == "8":
                self._test_mcp_tools_directly()
            elif choice == "9":
                print("Exiting...")
                break
            else:
                print("Invalid choice!")
    
    def _test_add_todo(self):
        title = input("Enter todo title: ")
        description = input("Enter description (optional): ")
        priority = input("Enter priority (low/medium/high): ") or "medium"
        
        todo = self.storage.add_todo(title, description, priority)
        print(f"Added todo #{todo.id}: {todo.title}")
    
    def _test_list_todos(self):
        todos = self.storage.get_all_todos()
        if not todos:
            print("No todos found!")
            return
        
        print("\nTodo List:")
        for todo in todos:
            status = "Completed" if todo.completed else "Pending"
            priority_emoji = {"low": "Low", "medium": "Medium", "high": "High"}[todo.priority]
            print(f"#{todo.id} [{status}] [{priority_emoji}] {todo.title}")
            if todo.description:
                print(f"    {todo.description}")
    
    def _test_complete_todo(self):
        try:
            todo_id = int(input("Enter todo ID to complete: "))
            todo = self.storage.complete_todo(todo_id)
            if todo:
                print(f"Completed todo #{todo.id}: {todo.title}")
            else:
                print(f"Todo #{todo_id} not found!")
        except ValueError:
            print("Please enter a valid number!")
    
    def _test_get_todo(self):
        try:
            todo_id = int(input("Enter todo ID: "))
            todo = self.storage.get_todo(todo_id)
            if todo:
                print(f"\nTodo #{todo.id}")
                print(f"Title: {todo.title}")
                print(f"Description: {todo.description or 'None'}")
                print(f"Status: {'Completed' if todo.completed else 'Pending'}")
                print(f"Priority: {todo.priority}")
                print(f"Created: {todo.created_at}")
                if todo.completed_at:
                    print(f"Completed: {todo.completed_at}")
            else:
                print(f"Todo #{todo_id} not found!")
        except ValueError:
            print("Please enter a valid number!")
    
    def _test_update_todo(self):
        try:
            todo_id = int(input("Enter todo ID to update: "))
            print("Enter new values (press Enter to skip):")
            title = input("New title: ") or None
            description = input("New description: ") or None
            priority = input("New priority (low/medium/high): ") or None
            
            updates = {}
            if title: updates['title'] = title
            if description: updates['description'] = description
            if priority: updates['priority'] = priority
            
            if updates:
                todo = self.storage.update_todo(todo_id, **updates)
                if todo:
                    print(f"Updated todo #{todo.id}: {todo.title}")
                else:
                    print(f"Todo #{todo_id} not found!")
            else:
                print("No updates provided!")
        except ValueError:
            print("Please enter a valid number!")
    
    def _test_delete_todo(self):
        try:
            todo_id = int(input("Enter todo ID to delete: "))
            success = self.storage.delete_todo(todo_id)
            if success:
                print(f"Deleted todo #{todo_id}")
            else:
                print(f"Todo #{todo_id} not found!")
        except ValueError:
            print("Please enter a valid number!")
    
    def _test_persistence(self):
        print("Testing persistence...")
        original_count = len(self.storage.get_all_todos())
        
        # Create new storage instance
        new_storage = TodoStorage("test_todos.json")
        new_count = len(new_storage.get_all_todos())
        
        if original_count == new_count:
            print(f"Persistence test passed! {new_count} todos survived restart")
        else:
            print(f"Persistence test failed! {original_count} vs {new_count}")
    
    def _test_mcp_tools_directly(self):
        """Test MCP tools directly using async calls"""
        async def run_mcp_test():
            from todo_server import handle_call_tool, handle_list_tools
            
            print("\nTesting MCP Tools Directly...")
            
            # Test list tools
            tools = await handle_list_tools()
            print(f"Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test add todo
            result = await handle_call_tool(
                "add_todo", 
                {"title": "MCP Test Todo", "description": "Testing MCP directly", "priority": "high"}
            )
            print(f"Add result: {result[0].text}")
            
            # Test list todos
            result = await handle_call_tool("list_todos", {})
            print(f"List result: {result[0].text}")
        
        # Run the async test
        try:
            asyncio.run(run_mcp_test())
        except Exception as e:
            print(f"MCP test failed: {e}")


def main():
    """Main test runner"""
    print("Todo MCP Server Test Suite")
    print("=" * 40)
    print("Choose testing method:")
    print("1. Unit tests (storage layer)")
    print("2. MCP tools tests (async)")
    print("3. Interactive tests")
    print("4. All automated tests")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        print("\nRunning Storage Unit Tests...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestTodoStorage)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    
    elif choice == "2":
        print("\nRunning MCP Tools Tests...")
        suite = unittest.TestSuite()
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMCPServer))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMCPToolsAsync))
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    
    elif choice == "3":
        print("\nRunning Interactive Tests...")
        runner = InteractiveTestRunner()
        runner.run_interactive_test()
    
    elif choice == "4":
        print("\nRunning All Automated Tests...")
        test_classes = [TestTodoStorage, TestMCPServer, TestMCPToolsAsync]
        suite = unittest.TestSuite()
        for test_class in test_classes:
            suite.addTests(unittest.TestLoader().loadTestsFromTestCase(test_class))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print(f"\nTest Results:")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        if result.testsRun > 0:
            success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
            print(f"Success rate: {success_rate:.1f}%")
    
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
