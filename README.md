# M. A.S. T.E.R. Memory System

Multi-Agent Synergized Task Execution with **Persistent Memory**

> Phase 1: Memory System - 记忆系统实现

## 🌟 特性

- **可插拔后端**：支持 Qdrant (向量数据库) / Builtin (本地文件) 多种存储
- **混合检索**：稠密 + 稀疏向量混合搜索
- **LLM 抽取**：自动从任务结果中抽取关键事实作为记忆
- **上下文注入**：智能检索相关记忆并注入到 AI 上下文

## 📦 安装

```bash
pip install -r requirements.txt
```

## 🚀 快速开始

### 1. 使用 Qdrant 后端

```python
import asyncio
from memory import QdrantMemory, MemoryRetriever, AddMemoryRequest

# 初始化
memory = QdrantMemory(host="localhost", port=6333)

# 创建检索器
retriever = MemoryRetriever(memory, max_context_memories=3)

async def main():
    # 添加记忆
    await memory.add(AddMemoryRequest(
        bot_id="agent_001",
        content="用户喜欢科幻小说，尤其是《三体》和《基地》系列",
        metadata={"source": "chat", "topic": "preferences"}
    ))
    
    # 检索记忆
    context = await retriever.retrieve("agent_001", "用户有什么阅读偏好?")
    print(context.to_prompt_context())

asyncio.run(main())
```

### 2. 使用本地文件后端

```python
from memory import BuiltinMemory

# 使用本地文件存储（无需额外依赖）
memory = BuiltinMemory(storage_path="./data/memory", mode="sparse")
```

### 3. 记忆自动抽取

```python
from memory import MemoryExtractor

# 创建抽取器（需要 LLM 客户端）
extractor = MemoryExtractor(llm_client=openai_client)

# 从任务结果中抽取记忆
facts = await extractor.extract(
    task_result="成功完成了用户的数据分析任务，生成了销售报告。报告包含华东区Q1销量同比增长25%的数据。",
    task_description="数据分析任务"
)

print(facts.facts)  # ['华东区Q1销量同比增长25%', ...]
print(facts.tags)   # ['销售报告', '数据分析', '华东区', ...]
```

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System Architecture               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户任务 → LLM 抽取关键事实 → 向量存储 (Qdrant/Builtin)    │
│                                                             │
│  新任务 → 混合检索 → 上下文注入 → AI 执行                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Provider (接口抽象)                                        │
│  ├── QdrantMemory (向量数据库)                              │
│  ├── BuiltinMemory (本地文件: off/sparse/dense)            │
│  └── (可扩展: Mem0, OpenViking)                            │
├─────────────────────────────────────────────────────────────┤
│  Extractor (LLM 事实抽取)                                   │
│  Retriever (智能检索 + 上下文注入)                          │
└─────────────────────────────────────────────────────────────┘
```

## 📁 文件结构

```
phase1-memory/
├── backend/
│   └── memory/
│       ├── __init__.py           # 模块导出
│       ├── provider.py           # Provider 接口定义
│       ├── qdrant_backend.py     # Qdrant 实现
│       ├── builtin_backend.py    # 本地文件实现
│       ├── extractor.py          # LLM 事实抽取
│       └── retriever.py          # 检索器
├── requirements.txt
├── package.json
└── README.md
```

## 🔧 配置

### Qdrant

```python
memory = QdrantMemory(
    host="localhost",
    port=6333,
    api_key="your-api-key",  # 可选
    vector_size=1536,        # OpenAI ada-002 默认维度
    distance="Cosine",       # 距离度量
)
```

### Builtin 本地存储

```python
memory = BuiltinMemory(
    storage_path="./data/memory",
    mode="sparse",  # off / sparse / dense
)
```

| 模式 | 说明 | 依赖 |
|:---|:---|:---|
| off | 仅文件索引，无向量搜索 | 无 |
| sparse | TF-IDF 稀疏向量 | scikit-learn |
| dense | 语义向量 | sentence-transformers |

## 📝 License

MIT License