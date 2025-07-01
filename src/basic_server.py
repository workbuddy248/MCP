import asyncio
import json
import sys
from typing import Any, Dict

# Basic MCP server without FastMCP
class BasicMCPServer:
    def __init__(self):
        self.tools = {
            "parse_test_instructions": self.parse_test_instructions,
            "list_active_sessions": self.list_active_sessions
        }
        self.sessions = {}
    
    async def parse_test_instructions(self, prompt: str, url: str = "", username: str = "", password: str = ""):
        """Parse test instructions"""
        session_id = f"session_{len(self.sessions) + 1}"
        
        # Simple parsing logic
        steps = [
            {"action": "navigate", "target": url or "https://example.com", "description": f"Navigate to {url}"},
            {"action": "fill", "target": "username", "value": username, "description": "Fill username"},
            {"action": "fill", "target": "password", "value": password, "description": "Fill password"},
            {"action": "click", "target": "login button", "description": "Click login"}
        ]
        
        self.sessions[session_id] = {
            "prompt": prompt,
            "url": url,
            "steps": steps,
            "status": "planned"
        }
        
        return {
            "session_id": session_id,
            "status": "success",
            "steps_count": len(steps),
            "message": f"Created test plan with {len(steps)} steps"
        }
    
    async def list_active_sessions(self):
        """List active sessions"""
        return {
            "sessions": list(self.sessions.keys()),
            "count": len(self.sessions),
            "message": f"Found {len(self.sessions)} sessions"
        }
    
    async def handle_request(self, request):
        """Handle MCP request"""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            
            if method == "tools/list":
                return {
                    "tools": [
                        {
                            "name": "parse_test_instructions",
                            "description": "Parse natural language test instructions",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "prompt": {"type": "string"},
                                    "url": {"type": "string"},
                                    "username": {"type": "string"},
                                    "password": {"type": "string"}
                                },
                                "required": ["prompt"]
                            }
                        },
                        {
                            "name": "list_active_sessions",
                            "description": "List all active test sessions",
                            "inputSchema": {"type": "object", "properties": {}}
                        }
                    ]
                }
            
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                
                if tool_name in self.tools:
                    result = await self.tools[tool_name](**arguments)
                    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                else:
                    return {"error": f"Unknown tool: {tool_name}"}
            
            elif method == "initialize":
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "e2e-testing-server",
                        "version": "0.1.0"
                    }
                }
            
            return {"error": f"Unknown method: {method}"}
            
        except Exception as e:
            return {"error": str(e)}

async def main():
    """Run basic MCP server"""
    server = BasicMCPServer()
    
    print("Starting basic MCP server...", file=sys.stderr)
    
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                response["id"] = request.get("id")
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": str(e)
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("Server stopped", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
