# M. A. S. T. E. R.
## Multi-Agent Synergized Task Execution with Persistent Memory

> Windows 一键启动版 | 多渠道支持

---## ⚡ 快速开始### 1. 下载ZIP 包并解压到任意位置### 2. 安装
双击 `install. bat`，等待自动完成### 3. 启动
双击 `启动 MASTER. bat`### 4. 使用
浏览器自动打开 http://localhost:3---

## 📋 首次配置### 配置 AI API Key1. 打开 `config. example. py`2. 填入你的 API Key（至少一个）：
   - OpenAI: `OPENAI_API_KEY = "sk-..."`   - Claude: `ANTHROPIC_API_KEY = "sk- ant-..."`
3. 另存为 `config. py`

### 启用向量搜索（可选）
如果需要语义记忆功能：
1. 下载 Qdrant: https://github. com/ qdrant/qdrant/releases2. 解压后运行 `qdrant. exe`3. 修改 `config. py` 中 `MEMORY_BACKEND = "qdrant"`

---## 🎯 功能
| 功能 | 状态 | 说明 |
|:---|:---|:---|  | 多 AI 协作 | ✅ | 决策 AI 调度多个垂直 AI |
| 记忆系统 | ✅ | 跨任务持久记忆 |
| MCP 支持 | ✅ | 标准化工具协议 |
| 动态干预 | ✅ | 执行中插入要求 |
| 多渠道 | ✅ | Web/Telegram/Discord/飞书/Email |
---## 📁 文件说明

```MASTER/├── install. bat          # 双击安装（首次使用）├── 启动 MASTER. bat      # 双击启动
├── stop. bat             # 停止服务├── config. example. py   # 配置示例├── backend/│   ├── memory/        # 记忆系统│   ├── mcp/           # MCP 工具协议│   └── channels/      # 多渠道适配器│       ├── telegram_ adapter. py│       ├── discord_ adapter. py│       ├── feishu_ adapter. py│       ├── email_ adapter. py│       └── local_ adapter. py└── data/                 # 数据存储
```---## 📡 渠道配置示例### Telegram```pythonChannelConfig(    channel_type=ChannelType.TELEGRAM,
    bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",    enabled=True,)```### Discord```pythonChannelConfig(    channel_type=ChannelType.DISCORD,    bot_token="YOUR_DISCORD_BOT_TOKEN",    enabled=True,)```### 飞书```pythonChannelConfig(    channel_type=ChannelType.FEISHU,    api_key="YOUR_APP_ID",    api_secret="YOUR_APP_SECRET",    enabled=True,)```### Email (SMTP)```pythonChannelConfig(    channel_type=ChannelType.EMAIL,    api_key="your_email@gmail.com",    api_secret="your_app_password",    metadata={        "smtp_host": "smtp.gmail.com",        "smtp_port": 587,        "use_tls": True,    },    enabled=True,)```---## ❓ 常见问题

**Q: 提示 "未检测到 Python"**
> 下载安装 Python: https://www. python.org/downloads/> 记得勾选 "Add Python to PATH"**Q: 启动后显示错误**> 1. 检查 API Key 是否配置正确
> 2. 检查端口是否被占用: `netstat -ano | findstr 8`**Q: 如何停止服务?**
> 双击 `stop. bat`**Q: 想删除所有数据?**
> 删除 `data` 文件夹---## 🔧 技术支持- GitHub: https://github.com/hutaodetao/MASTER- 问题反馈: GitHub Issues---## 📝 LicenseMIT License