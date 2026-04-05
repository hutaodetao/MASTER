# MCP (Model Context Protocol) 支持
# Phase 2: 标准化工具协议接入

## 目标
- MCP Client：连接外部 MCP 服务器
- 内置 MCP Server：提供文件系统、浏览器等工具
- 工具注册与发现

## 实现计划

### 1. MCP Client
```python
# mcp/client.py
class MCPClient:
    """MCP 客户端，连接到 MCP 服务器"""
    
    def connect(self, server_url: str): ...
    def list_tools(self) -> list[Tool]: ...
    async def call_tool(self, name: str, args: dict): ...
```

### 2. MCP Server (内置)
```python
# mcp/server/
# - filesystem.py  文件系统工具
# - browser.py    Playwright 浏览器工具
# - database.py   数据库工具
```

### 3. 工具网关
```python
# mcp/gateway.py
class ToolGateway:
    """统一工具入口"""
    
    def register_mcp(self, server_name: str, client: MCPClient): ...
    def call_tool(self, tool_name: str, args: dict): ...
```

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    M.A. S.T. E.R.                           │
├─────────────────────────────────────────────────────────────┤
│  Decision AI → Tool Gateway → MCP Client                   │
│                            ↓                                │
│                     MCP Server                              │
│                  (filesystem / browser / database)          │
└─────────────────────────────────────────────────────────────┘
```

开始实现？