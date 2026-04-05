"""
Memory Provider Abstract Interface
参考 Memoh: internal/memory/adapters/provider. go
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class MemoryBackendType(str, Enum):
    """支持的记忆后端类型"""
    QDRANT = "qdrant"
    BUILTIN_SPARSE = "builtin_sparse"
    BUILTIN_DENSE = "builtin_dense"
    BUILTIN_OFF = "builtin_off"
    MEM0 = "mem0"
    OPENVIKING = "openviking"


@dataclass
class MemoryItem:
    """单条记忆"""
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class MemorySearchResult:
    """记忆搜索结果"""
    items: list[MemoryItem]
    total: int
    query: str
    scores: list[float] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "total": self.total,
            "query": self.query,
            "scores": self.scores,
        }


@dataclass
class AddMemoryRequest:
    """添加记忆请求"""
    bot_id: str  # 对应 Memoh 的 bot_id
    content: str
    metadata: dict = field(default_factory=dict)
    # 可选：指定向量（如果后端支持）
    vector: list[float] | None = None


@dataclass
class SearchMemoryRequest:
    """搜索记忆请求"""
    bot_id: str
    query: str
    limit: int = 5
    filters: dict | None = None
    # 可选：预计算的查询向量
    query_vector: list[float] | None = None


@dataclass
class UpdateMemoryRequest:
    """更新记忆请求"""
    memory_id: str
    content: str | None = None
    metadata: dict | None = None


class MemoryProvider(ABC, Generic[T]):
    """
    记忆提供者抽象接口
    参考 Memoh 的 Provider 接口设计
    """
    
    @property
    @abstractmethod
    def backend_type(self) -> MemoryBackendType:
        """返回后端类型标识"""
        pass
    
    @abstractmethod
    async def add(self, request: AddMemoryRequest) -> MemorySearchResult:
        """
        添加新记忆
        相当于 Memoh 的 Add 方法
        """
        pass
    
    @abstractmethod
    async def search(self, request: SearchMemoryRequest) -> MemorySearchResult:
        """
        搜索记忆
        混合检索（稠密+稀疏）
        """
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> MemoryItem | None:
        """获取单条记忆"""
        pass
    
    @abstractmethod
    async def update(self, request: UpdateMemoryRequest) -> MemoryItem:
        """更新记忆"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
    
    @abstractmethod
    async def get_all(self, bot_id: str, limit: int = 100) -> MemorySearchResult:
        """获取某机器人的所有记忆"""
        pass
    
    @abstractmethod
    async def delete_all(self, bot_id: str) -> int:
        """删除某机器人的所有记忆"""
        pass
    
    async def compact(self, bot_id: str, ratio: float = 0.7) -> dict:
        """
        记忆压缩（合并相似条目）
        可选实现
        """
        raise NotImplementedError()
    
    async def usage(self, bot_id: str) -> dict:
        """
        记忆使用统计
        可选实现
        """
        raise NotImplementedError()
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


class MemoryProviderFactory:
    """记忆提供者工厂"""
    
    _providers: dict[MemoryBackendType, type[MemoryProvider]] = {}
    
    @classmethod
    def register(cls, backend_type: MemoryBackendType, provider_class: type[MemoryProvider]):
        """注册后端提供者"""
        cls._providers[backend_type] = provider_class
    
    @classmethod
    def create(cls, backend_type: MemoryBackendType, **config) -> MemoryProvider:
        """创建后端提供者实例"""
        if backend_type not in cls._providers:
            raise ValueError(f"Unknown backend type: {backend_type}")
        return cls._providers[backend_type](**config)


# 注册内置后端
from .qdrant_backend import QdrantMemory
from .builtin_builtin import BuiltinMemory

MemoryProviderFactory.register(MemoryBackendType.QDRANT, QdrantMemory)
MemoryProviderFactory.register(MemoryBackendType.BUILTIN_SPARSE, BuiltinMemory)
MemoryProviderFactory.register(MemoryBackendType.BUILTIN_DENSE, BuiltinMemory)
MemoryProviderFactory.register(MemoryBackendType.BUILTIN_OFF, BuiltinMemory)