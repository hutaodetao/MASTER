# M. A. S. T. E. R. 配置文件
# 复制此文件为 config. py 并填入你的配置

# =================== AI 配置 ===================
# 至少需要一个 API Key

# OpenAI
OPENAI_API_KEY = ""  # 填入: sk-...

# Anthropic (Claude)
ANTHROPIC_API_KEY = ""  # 填入: sk-ant-...

# DeepSeek
DEEPSEEK_API_KEY = ""

# Moonshot (月之暗面)
MOONSHOT_API_KEY = ""

# =================== 服务配置 ===================
HOST = "127.0.0.1"
PORT = 8000

# =================== 记忆系统配置 ===================
# 记忆后端类型: qdrant / builtin_sparse / builtin_dense / builtin_off
MEMORY_BACKEND = "builtin_sparse"
MEMORY_STORAGE_PATH = "./data/memory"

# Qdrant 配置（如果使用 qdrant 后端）
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_API_KEY = ""  # 可选

# =================== MCP 配置 ===================
# 内置 MCP 服务器配置
MCP_SERVERS = [
    # 示例：文件系统 MCP
    # {
    #     "name": "filesystem",
    #     "command": "npx",
    #     "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
    # },
]

# =================== 日志配置 ===================
LOG_LEVEL = "INFO"