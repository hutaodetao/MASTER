"""
MCP Tool Gateway
统一工具入口，管理多个 MCP 客户端
"""
from dataclasses import dataclass, field
from typing import Any
from .client import MCPClient, ToolDefinition, ToolCallResult, TransportType
 
  
@dataclass
class MCPServerConfig:  # MCP 服务器配置
    """MCP 服务器配置"""
    name: str
    transport: TransportType
    # Stdio 配置
    command: str | None = None
    args: list[str] | None = None
    env: dict | None = None
    # HTTP 配置
    url: str | None = None
    api_key: str | None = None
 
  
class ToolGateway:  # 工具网关
    """
    统一工具入口
    支持多 MCP 服务器注册和工具调用
    """    
    def __init__(self):
        self._servers: dict[str, MCPClient] = {}  # name -> client
        self._tools_cache: dict[str, ToolDefinition] = {}  # tool_name -> definition
    
    @property
    def servers(self) -> dict[str, MCPClient]:
        """已连接的服务器"""
        return self._servers
    
    async def register_server(self, config: MCPServerConfig) -> MCPClient:  # 注册 MCP 服务器
        """
        注册 MCP 服务器        
        Args:            config: 服务器配置            Returns:            MCPClient 实例
        """        client = MCPClient()        
        if config.transport == TransportType.STDIO:
            await client.connect_stdio(
                command=config.command,                args=config.args,                env=config.env,
            )        elif config.transport == TransportType.HTTP:
            await client.connect_http(                    url=config.url,                    api_key=config.api_key,                )
        else:            raise ValueError(f"Unsupported transport: {config.transport}")
        
        # 存储服务器
        self._servers[config.name] = client        
        # 缓存工具        for tool in client.tools:            self._tools_cache[f"{config.name}/{tool.name}"] = tool
        
        return client
    
    async def unregister_server(self, name: str) -> bool:  # 注销服务器
        """注销 MCP 服务器"""
        if name in self._servers:            client = self._servers.pop(name)
            await client.close()
            
            # 移除相关工具            to_remove = [k for k in self._tools_cache if k.startswith(f"{name}/")]
            for k in to_remove:
                del self._tools_cache[k]
            
            return True
        return False
    
    def get_tool(self, full_name: str) -> ToolDefinition | None:  # 获取工具定义
        """获取工具定义（支持 server/tool_name 格式）"""
        if "/" in full_name:
            return self._tools_cache.get(full_name)
        # 尝试前缀匹配        for key, tool in self._tools_cache.items():
            if key.endswith(f"/{full_name}"):
                return tool
        return None
    
    def list_all_tools(self) -> list[dict]:
        """列出所有工具"""
        result = []
        for full_name, tool in self._tools_cache.items():            server_name = full_name.split("/")[0] if "/" in full_name else "builtin"
            result.append({                "full_name": full_name,
                "server": server_name,
                "name": tool.name,                "description": tool.description,
                "schema": tool.input_schema,            })
        return result
    
    async def call_tool(  # 调用工具
        self,        tool_name: str,        arguments: dict = None,
        server_name: str = None,  # 可选，指定服务器
    ) -> ToolCallResult:        """
        调用工具
        Args:            tool_name: 工具名（可包含服务器前缀，如 "filesystem/read_file"）            arguments: 工具参数            server_name: 可选，指定服务器            Returns:            ToolCallResult
        """
        # 确定服务器        if server_name:            if server_name not in self._servers:                return ToolCallResult(                    tool_name=tool_name,                    error=f"Server {server_name} not found",                    is_error=True,                )            client = self._servers[server_name]            full_name = tool_name        else:            # 自动查找工具            tool = self.get_tool(tool_name)
            if tool is None:                return ToolCallResult(                    tool_name=tool_name,
                    error=f"Tool {tool_name} not found",                    is_error=True,                )            # 找到工具所属服务器
            for full_name, t in self._tools_cache.items():                if t.name == tool_name:                    server_name = full_name.split("/")[0] if "/" in full_name else "builtin"                    break            client = self._servers.get(server_name)            if client is None:
                return ToolCallResult(                    tool_name=tool_name,                    error=f"Server {server_name} not found",                    is_error=True,                )            full_name = tool.name
        
        return await client.call_tool(tool_name, arguments)
    
    async def call_tool_formatted(  # 格式化调用结果
        self,        tool_name: str,        arguments: dict = None,
    ) -> str:        """调用工具并格式化结果"""
        result = await self.call_tool(tool_name, arguments)        
        if result.is_error:            return f"❌ Error: {result.error}"
        
        # 简单格式化        if isinstance(result.result, str):            return result.result
        
        import json        return json.dumps(result.result, ensure_ascii=False, indent=2)
    
    async def close_all(self):  # 关闭所有服务器
        """关闭所有 MCP 服务器连接"""
        for client in self._servers.values():
            await client.close()
        self._servers.clear()        self._tools_cache.clear()
    
    def get_server_status(self) -> list[dict]:  # 获取服务器状态
        """获取所有服务器状态"""
        status = []        for name, client in self._servers.items():            status.append({                "name": name,                "connected": True,                "tools_count": len(client.tools),
                "server_info": client.server_info.get("serverInfo", {}),            })
        return status


class BuiltinToolProvider:  # 内置工具提供者
    """
    内置工具（无需 MCP 服务器）    包含基础的文件系统、搜索等工具
    """    
    def __init__(self, gateway: ToolGateway):        self.gateway = gateway
    
    def register_builtin_tools(self):  # 注册内置工具
        """注册内置工具到网关"""
        # 这里可以添加一些不需要 MCP 服务器的内置工具
        # 例如：时间、随机数等简单工具
        pass