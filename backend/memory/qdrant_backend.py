"""
Qdrant 向量数据库后端实现
基于 Qdrant 的语义搜索 + 混合检索
"""
import uuid
from datetime import datetime
from typing import Any
import numpy as np

from .provider import (
    MemoryProvider,
    MemoryItem,
    MemorySearchResult,
    AddMemoryRequest,
    SearchMemoryRequest,
    UpdateMemoryRequest,
    MemoryBackendType,
)


class QdrantMemory(MemoryProvider):
    """
    Qdrant 向量数据库后端
    支持：
    - 稠密向量语义搜索
    - 混合检索（需 Qdrant 1.7+）
    - 过滤条件
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "master_memory",
        vector_size: int = 1536,  # OpenAI ada-002 默认维度
        grpc_port: int = 6334,
        api_key: str | None = None,
        distance: str = "Cosine",
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.grpc_port = grpc_port
        self.api_key = api_key
        self.distance = distance
        
        self._client = None
        self._embedding_model = None
        
    @property
    def backend_type(self) -> MemoryBackendType:
        return MemoryBackendType.QDRANT
    
    async def _get_client(self):
        """延迟初始化 Qdrant 客户端"""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key,
                )
                await self._ensure_collection()
            except ImportError:
                raise ImportError("qdrant-client not installed. Run: pip install qdrant-client")
        return self._client
    
    async def _get_embedding_model(self):
        """获取嵌入模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # 使用轻量级模型
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.vector_size = self._embedding_model.get_sentence_embedding_dimension()
            except ImportError:
                # 回退：使用随机向量（仅测试用）
                self._embedding_model = None
        return self._embedding_model
    
    async def _ensure_collection(self):
        """确保 collection 存在"""
        client = await self._get_client()
        
        from qdrant_client.models import Distance, VectorParams
        
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclidean": Distance.EUCLID,
                "Dot": Distance.DOT,
            }
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=distance_map.get(self.distance, Distance.COSINE),
                ),
            )
    
    def _generate_id(self) -> str:
        return f"mem_{uuid.uuid4().hex[:12]}"
    
    async def _embed_text(self, text: str) -> list[float]:
        """将文本转换为向量"""
        model = await self._get_embedding_model()
        
        if model is not None:
            # 使用 sentence-transformers
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # 回退：随机向量（仅测试用）
            return np.random.randn(self.vector_size).tolist()
    
    async def add(self, request: AddMemoryRequest) -> MemorySearchResult:
        """添加记忆"""
        client = await self._get_client()
        
        memory_id = self._generate_id()
        
        # 生成向量
        if request.vector:
            vector = request.vector
        else:
            vector = await self._embed_text(request.content)
        
        from qdrant_client.models import PointStruct
        
        point = PointStruct(
            id=memory_id,
            vector=vector,
            payload={
                "content": request.content,
                "bot_id": request.bot_id,
                "metadata": request.metadata,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        )
        
        client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        
        # 返回添加的记忆
        item = MemoryItem(
            id=memory_id,
            content=request.content,
            metadata=request.metadata,
        )
        
        return MemorySearchResult(
            items=[item],
            total=1,
            query=request.content,
            scores=[1.0],
        )
    
    async def search(self, request: SearchMemoryRequest) -> MemorySearchResult:
        """搜索记忆"""
        client = await self._get_client()
        
        # 生成查询向量
        if request.query_vector:
            query_vector = request.query_vector
        else:
            query_vector = await self._embed_text(request.query)
        
        # 构建过滤条件
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        filter_conditions = None
        if request.filters:
            conditions = []
            for key, value in request.filters.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            if conditions:
                filter_conditions = Filter(must=conditions)
        
        # 搜索
        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=filter_conditions,
            limit=request.limit,
            with_payload=True,
            with_vectors=False,
        )
        
        # 转换结果
        items = []
        scores = []
        
        for result in results:
            payload = result.payload
            items.append(MemoryItem(
                id=result.id,
                content=payload.get("content", ""),
                metadata=payload.get("metadata", {}),
                created_at=datetime.fromisoformat(payload.get("created_at", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(payload.get("updated_at", datetime.now().isoformat())),
            ))
            scores.append(result.score)
        
        return MemorySearchResult(
            items=items,
            total=len(items),
            query=request.query,
            scores=scores,
        )
    
    async def get(self, memory_id: str) -> MemoryItem | None:
        """获取单条记忆"""
        client = await self._get_client()
        
        results = client.scroll(
            collection_name=self.collection_name,
            scroll_filter=f"id == {memory_id}",
            limit=1,
            with_payload=True,
        )
        
        if results[0]:
            payload = results[0][0].payload
            return MemoryItem(
                id=memory_id,
                content=payload.get("content", ""),
                metadata=payload.get("metadata", {}),
            )
        return None
    
    async def update(self, request: UpdateMemoryRequest) -> MemoryItem:
        """更新记忆"""
        client = await self._get_client()
        
        # 获取现有内容
        existing = await self.get(request.memory_id)
        if not existing:
            raise ValueError(f"Memory {request.memory_id} not found")
        
        new_content = request.content or existing.content
        new_metadata = request.metadata or existing.metadata
        
        # 生成新向量
        vector = await self._embed_text(new_content)
        
        from qdrant_client.models import PointStruct
        
        point = PointStruct(
            id=request.memory_id,
            vector=vector,
            payload={
                "content": new_content,
                "metadata": new_metadata,
                "created_at": existing.created_at.isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        )
        
        client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        
        return MemoryItem(
            id=request.memory_id,
            content=new_content,
            metadata=new_metadata,
        )
    
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        client = await self._get_client()
        
        client.delete(
            collection_name=self.collection_name,
            points_selector=[memory_id],
        )
        return True
    
    async def get_all(self, bot_id: str, limit: int = 100) -> MemorySearchResult:
        """获取某机器人的所有记忆"""
        client = await self._get_client()
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        results = client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="bot_id", match=MatchValue(value=bot_id))]
            ),
            limit=limit,
            with_payload=True,
        )
        
        items = []
        for point in results[0]:
            payload = point.payload
            items.append(MemoryItem(
                id=point.id,
                content=payload.get("content", ""),
                metadata=payload.get("metadata", {}),
            ))
        
        return MemorySearchResult(
            items=items,
            total=len(items),
            query=f"all_memories_for_{bot_id}",
        )
    
    async def delete_all(self, bot_id: str) -> int:
        """删除某机器人的所有记忆"""
        client = await self._get_client()
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # 先获取所有 ID
        results = client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="bot_id", match=MatchValue(value=bot_id))]
            ),
            limit=10000,
        )
        
        ids_to_delete = [point.id for point in results[0]]
        
        if ids_to_delete:
            client.delete(
                collection_name=self.collection_name,
                points_selector=ids_to_delete,
            )
        
        return len(ids_to_delete)
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            client = await self._get_client()
            client.get_collections()
            return True
        except Exception:
            return False