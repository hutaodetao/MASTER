# M. A. S. T. E. R. 系统配置及功能总结

> Multi-Agent Synergized Task Execution with Persistent Memory
> 多智能体协同任务执行系统

---

## 📋 目录

1. [系统架构](#1-系统架构)
2. [安装配置](#2-安装配置)
3. [功能模块](#3-功能模块)
4. [渠道配置](#4-渠道配置)
5. [记忆系统](#5-记忆系统)
6. [MCP 工具协议](#6-mcp-工具协议)
7. [快速开始](#7-快速开始)
8. [文件结构](#8-文件结构)

---

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            M. A. S. T. E. R.                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   用户入口   │    │   用户入口   │    │   用户入口   │                 │
│  │  Web UI     │    │  Telegram   │    │  Discord    │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                  │                        │
│         └──────────────────┼──────────────────┘                        │
│                            ↓                                           │
│                   ┌────────────────┐                                   │
│                   │  消息分发器     │                                   │
│                   │ MessageDispatcher │                                │
│                   └────────┬───────┘                                   │
│                            ↓                                           │
│         ┌──────────────────┼──────────────────┐                        │
│         ↓                  ↓                  ↓                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                  │
│  │  决策 AI     │   │  任务调度   │   │  成果融合   │                  │
│  │ Decision    │   │  Dispatcher │   │  Integrator │                  │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                  │
│         │                 │                 │                          │
│         └─────────────────┼─────────────────┘                          │
│                           ↓                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     AI 节点池                                    │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                    │   │
│  │  │Writer  │ │ Logic  │ │Search  │ │ Coder  │                    │   │
│  │  │(写作)  │ │(逻辑)  │ │(检索)  │ │(编程)  │                    │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                           ↓                                            │
│         ┌─────────────────┴─────────────────┐                          │
│         ↓                                   ↓                          │
│  ┌─────────────────┐              ┌─────────────────┐                 │
│  │   记忆系统       │              │   MCP 工具      │                 │
│  │   Memory        │              │   Gateway       │                 │
│  └─────────────────┘              └─────────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 安装配置

### 2.1 环境要求

| 要求 | 规格 |
|:---|:---|
| 操作系统 | Windows 10/11 或 Linux/macOS |
| Python | 3.11+ |
| 内存 | 推荐 4GB+ |
| 存储 | 至少 1GB 可用空间 |

### 2.2 Windows 一键安装

1. **下载**：从 GitHub 下载 ZIP 包
2. **安装**：双击 `install. bat`
3. **启动**：双击 `启动 MASTER. bat`
4. **访问**：浏览器打开 http://localhost:3

### 2.3 配置文件

复制 `config. example. py` 为 `config. py` 并配置：

```python
# =================== AI 配置 ===================
OPENAI_API_KEY = "sk-..."        # OpenAI
ANTHROPIC_API_KEY = "sk-ant-..." # Claude

# =================== 服务配置 ===================
HOST = "127.0.0.1"
PORT = 8

# =================== 记忆系统 ===================
MEMORY_BACKEND = "builtin_sparse"  # qdrant / builtin_sparse / builtin_dense / builtin_off
QDRANT_HOST = "localhost"
QDRANT_PORT = 6
```

---

## 3. 功能模块

### 3.1 核心功能

| 功能 | 说明 | 状态 |
|:---|:---|:---|
| **多 AI 协作** | 决策 AI 调度多个垂直领域 AI | ✅ |
| **记忆系统** | 跨任务持久记忆，向量检索 | ✅ |
| **MCP 协议** | 标准化工具协议扩展 | ✅ |
| **动态干预** | 执行中插入要求，实时调整 | ✅ |
| **多渠道** | Web/Telegram/Discord/飞书/Email | ✅ |

### 3.2 协作模式

| 模式 | 说明 |
|:---|:---|
| **标准分工** | 决策 AI 拆解 → 分发 → 汇总 |
| **讨论共识** | 多 AI 循环讨论，达成一致 |
| **评审团** | 多 AI 独立完成，互评打分 |

### 3.3 动态干预

| 干预类型 | 说明 |
|:---|:---|
| `insert` | 新增要求，追加到下一轮 |
| `modify` | 修改要求，可能需回退 |
| `context_add` | 补充上下文，不改流程 |
| `adjust` | 调整方向，重新规划 |

---

## 4. 渠道配置

### 4.1 支持的渠道

| 渠道 | 状态 | 按钮 | 卡片 | 配置项 |
|:---|:---|:---|:---|:---|
| Web UI | ✅ | ✅ | ✅ | 内置 |
| Telegram | ✅ | ✅ | ❌ | bot_token |
| Discord | ✅ | ❌ | ✅ | bot_token |
| 飞书 | ✅ | ✅ | ✅ | app_id, app_secret |
| Email | ✅ | ❌ | ❌ | smtp 配置 |

### 4.2 渠道配置示例

**Telegram**
```python
ChannelConfig(
    channel_type=ChannelType.TELEGRAM,
    bot_token="123456:ABC-DEF...",
    enabled=True,
)
```

**飞书**
```python
ChannelConfig(
    channel_type=ChannelType.FEISHU,
    api_key="APP_ID",
    api_secret="APP_SECRET",
    enabled=True,
)
```

**Email**
```python
ChannelConfig(
    channel_type=ChannelType.EMAIL,
    api_key="user@gmail.com",
    api_secret="app_password",
    metadata={
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
    },
)
```

---

## 5. 记忆系统

### 5.1 后端类型

| 后端 | 模式 | 依赖 | 适用场景 |
|:---|:---|:---|:---|
| **Qdrant** | 向量数据库 | Qdrant 服务 | 生产环境，精确语义搜索 |
| **Builtin (dense)** | 语义向量 | sentence-transformers | 中小规模，本地部署 |
| **Builtin (sparse)** | TF-IDF | scikit-learn | 轻量级，无需额外模型 |
| **Builtin (off)** | 关键词 | 无 | 最小化依赖 |

### 5.2 记忆流程

```
任务完成 → LLM 抽取关键事实 → 向量存储
                            ↓
新任务 → 混合检索 → 相关记忆 → 上下文注入 → AI 执行
```

---

## 6. MCP 工具协议

### 6.1 支持的传输方式

| 传输方式 | 说明 | 场景 |
|:---|:---|:---|
| **Stdio** | 标准输入输出 | 本地进程 |
| **HTTP** | REST API | 远程服务 |
| **SSE** | Server-Sent Events | 流式响应 |

### 6.2 MCP 服务器类型

可接入的 MCP 服务器：
- 文件系统 MCP
- 浏览器 MCP (Playwright)
- 数据库 MCP
- 自定义 MCP

### 6.3 使用示例

```python
from mcp import ToolGateway, MCPServerConfig, TransportType

gateway = ToolGateway()

# 注册 MCP 服务器
await gateway.register_server(MCPServerConfig(
    name="filesystem",
    transport=TransportType.STDIO,
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
))

# 调用工具
result = await gateway.call_tool("read_file", {"path": "/readme.txt"})
```

---

## 7. 快速开始

### 7.1 首次启动

```bash
# Windows
双击 install. bat
双击启动 MASTER. bat
```

### 7.2 访问系统

| 服务 | 地址 |
|:---|:---|
| 前端界面 | http://localhost:3 |
| 后端 API | http://127.0.0.1:8 |
| API 文档 | http://127.0.0.1:8/docs |

### 7.3 基本使用

1. 打开前端界面
2. 输入任务描述
3. AI 自动拆解并执行
4. 可在执行中插入新要求

---

## 8. 文件结构

```
MASTER/
├── install. bat              # 安装脚本
├── 启动 MASTER. bat          # 启动脚本
├── stop. bat                 # 停止脚本
├── config. example. py       # 配置示例
├── requirements. txt         # Python 依赖
├── README. md                # 说明文档
│
├── Backend/                  # 后端代码
│   ├── memory/               # 记忆系统
│   │   ├── provider. py      # Provider 接口
│   │   ├── qdrant_ backend. py
│   │   ├── builtin_ backend. py
│   │   ├── extractor. py     # 事实抽取
│   │   └── retriever. py     # 记忆检索
│   │
│   ├── mcp/                  # MCP 协议
│   │   ├── client. py        # MCP 客户端
│   │   └── gateway. py       # 工具网关
│   │
│   └── Channels/             # 多渠道
│       ├── adapter. py       # 适配器接口
│       ├── telegram_ adapter. py
│       ├── discord_ adapter. py
│       ├── feishu_ adapter. py
│       ├── email_ adapter. py
│       └── local_ adapter. py
│
├── Frontend/                 # 前端界面（待开发）
│
└── data/                     # 数据存储
    └── memory/               # 记忆数据
```

---

## 📞 技术支持

- GitHub: https://github.com/hutaodetao/MASTER
- 问题反馈: GitHub Issues

---

*文档版本: 1.0*  
*最后更新: 2026-04-05*