#!/usr/bin/env python3
"""
Test script for the MCP transcription server.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


async def test_mcp_server():
    """Test the MCP server functionality."""
    
    print("🧪 Testing MCP Transcription Server...")
    print("=" * 50)
    
    # Test 1: List tools
    print("\n1️⃣ Testing tool listing...")
    try:
        # Start the server process
        process = await asyncio.create_subprocess_exec(
            "python", "mcp_server.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send the request
        await process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.flush()
        
        # Read response
        response = await process.stdout.readline()
        print(f"✅ Server responded: {response.decode().strip()}")
        
        # Send list tools request
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        await process.stdin.write((json.dumps(list_tools_request) + "\n").encode())
        await process.stdin.flush()
        
        # Read response
        response = await process.stdout.readline()
        tools_response = json.loads(response.decode())
        
        if "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Error listing tools: {tools_response}")
        
        # Clean up
        process.terminate()
        await process.wait()
        
    except Exception as e:
        print(f"❌ Error testing server: {e}")
    
    # Test 2: Test supported formats
    print("\n2️⃣ Testing supported formats...")
    try:
        # Create a simple test file
        test_file = Path("test_audio.wav")
        test_file.write_bytes(b"fake audio data")
        
        # Test the get_supported_formats tool
        process = await asyncio.create_subprocess_exec(
            "python", "mcp_server.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        await process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.flush()
        await process.stdout.readline()  # Read init response
        
        # Call get_supported_formats
        call_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_supported_formats",
                "arguments": {}
            }
        }
        
        await process.stdin.write((json.dumps(call_request) + "\n").encode())
        await process.stdin.flush()
        
        response = await process.stdout.readline()
        call_response = json.loads(response.decode())
        
        if "result" in call_response:
            content = call_response["result"]["content"]
            print("✅ Supported formats retrieved successfully")
            print(f"   Response: {content[0]['text'][:100]}...")
        else:
            print(f"❌ Error calling tool: {call_response}")
        
        # Clean up
        process.terminate()
        await process.wait()
        
        # Remove test file
        test_file.unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Error testing formats: {e}")
    
    print("\n🎉 MCP Server test completed!")
    print("\nTo use with an MCP client:")
    print("1. Add mcp_config.json to your client configuration")
    print("2. Restart your MCP client")
    print("3. Try transcribing files through the AI assistant!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 