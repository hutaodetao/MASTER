"""
Builtin 本地记忆后端实现
支持三种模式：off / sparse / dense
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
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
 
 
class BuiltinMemory(MemoryProvider):
    """
    Builtin 本地记忆后端
    - off: 仅文件索引，无向量搜索
    - sparse: 本地神经稀疏向量（无API费用）
    - dense: 基于嵌入模型的语义搜索
    """
    
    def __init__(
        self,
        storage_path: str = "./data/memory",
        mode: str = "sparse",  # off / sparse / dense
        vectorizer_model: str | None = None,
    ):
        self.storage_path = Path(storage_path)
        self.mode = mode
        self.vectorizer_model = vectorizer_model
        
        # 确保目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._embedding_model = None
        self._sparse_encoder = None
        
    @property
    def backend_type(self) -> MemoryBackendType:
        mode_map = {
            "off": MemoryBackendType.BUILTIN_OFF,
            "sparse": MemoryBackendType.BUILTIN_SPARSE,
            "dense": MemoryBackendType.BUILTIN_DENSE,
        }
        return mode_map.get(self.mode, MemoryBackendType.BUILTIN_OFF)
    
    def _get_bot_dir(self, bot_id: str) -> Path:
        """获取机器人的记忆目录"""
        bot_dir = self.storage_path / bot_id
        bot_dir.mkdir(parents=True, exist_ok=True)
        return bot_dir
    
    def _load_index(self, bot_id: str) -> dict:
        """加载记忆索引"""
        index_file = self._get_bot_dir(bot_id) / "index.json"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"memories": [], "vectors": []}
    
    def _save_index(self, bot_id: str, index: dict):
        """保存记忆索引"""
        index_file = self._get_bot_dir(bot_id) / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    async def _get_sparse_encoder(self):
        """获取稀疏向量编码器（可选）"""
        if self._sparse_encoder is None and self.mode == "sparse":
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._sparse_encoder = TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2),
                )
            except ImportError:
                pass
        return self._sparse_encoder
    
    async def _get_embedding_model(self):
        """获取嵌入模型"""
        if self._embedding_model is None and self.mode == "dense":
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                pass
        return self._embedding_model
    
    def _generate_id(self) -> str:
        return f"mem_{uuid.uuid4().hex[:12]}"
    
    async def _embed_text(self, text: str) -> np.ndarray | None:
        """将文本转换为向量"""
        if self.mode == "off":
            return None
        
        if self.mode == "sparse":
            encoder = await self._get_sparse_encoder()
            if encoder is None:
                return None
            # 返回稀疏向量
            vec = encoder.transform([text])
            return np.asarray(vec.toarray())[0]
        
        if self.mode == "dense":
            model = await self._get_embedding_model()
            if model is None:
                return None
            return model.encode(text, convert_to_numpy=True)
        
        return None
    
    async def add(self, request: AddMemoryRequest) -> MemorySearchResult:
        """添加记忆"""
        memory_id = self._generate_id()
        
        # 保存记忆内容
        memory_file = self._get_bot_dir(request.bot_id) / f"{memory_id}.json"
        memory_data = {
            "id": memory_id,
            "content": request.content,
            "metadata": request.metadata,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        index = self._load_index(request.bot_id)
        
        # 计算向量
        vector = await self._embed_text(request.content)
        
        index["memories"].append({
            "id": memory_id,
            "content": request.content,
            "created_at": memory_data["created_at"],
        })
        
        if vector is not None:
            # 存储向量
            if "vectors" not in index:
                index["vectors"] = []
            index["vectors"].append(vector.tolist())
        
        self._save_index(request.bot_id, index)
        
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
        index = self._load_index(request.bot_id)
        
        if not index.get("memories"):
            return MemorySearchResult(items=[], total=0, query=request.query)
        
        # 模式：off - 仅关键词匹配
        if self.mode == "off":
            query_lower = request.query.lower()
            results = []
            for mem in index["memories"]:
                if query_lower in mem["content"].lower():
                    results.append((mem, 1.0))
            results = results[: request.limit]
            
            items = [
                MemoryItem(id=m["id"], content=m["content"], metadata={})
                for m, _ in results
            ]
            scores = [s for _, s in results]
            
            return MemorySearchResult(items=items, total=len(items), query=request.query, scores=scores)
        
        # 模式：sparse 或 dense - 向量相似度搜索
        query_vector = await self._embed_text(request.query)
        
        if query_vector is None or not index.get("vectors"):
            # 回退到关键词匹配
            return await self._search_by_keyword(request, index)
        
        # 计算余弦相似度
        vectors = np.array(index["vectors"])
        query_vec = query_vector.reshape(1, -1)
        
        # 归一化
        query_norm = np.linalg.norm(query_vec)
        vector_norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        
        # 避免除零
        vector_norms = np.where(vector_norms == 0, 1, vector_norms)
        query_norm = query_norm if query_norm > 0 else 1
        
        similarities = np.dot(vectors, query_vec.T).flatten() / (vector_norms.flatten() * query_norm)
        
        # 排序
        top_indices = np.argsort(similarities)[::-1][:request.limit]
        
        items = []
        scores = []
        
        for idx in top_indices:
            mem = index["memories"][idx]
            items.append(MemoryItem(
                id=mem["id"],
                content=mem["content"],
                metadata={},
            ))
            scores.append(float(similarities[idx]))
        
        return MemorySearchResult(items=items, total=len(items), query=request.query, scores=scores)
    
    async def _search_by_keyword(self, request: SearchMemoryRequest, index: dict) -> MemorySearchResult:
        """关键词搜索（回退方案）"""
        query_lower = request.query.lower()
        results = []
        
        for mem in index["memories"]:
            # 简单词匹配
            query_words = query_lower.split()
            content_lower = mem["content"].lower()
            matches = sum(1 for w in query_words if w in content_lower)
            if matches > 0:
                results.append((mem, matches / len(query_words)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[: request.limit]
        
        items = [MemoryItem(id=m["id"], content=m["content"], metadata={}) for m, _ in results]
        scores = [s for _, s in results]
        
        return MemorySearchResult(items=items, total=len(items), query=request.query, scores=scores)
    
    async def get(self, memory_id: str) -> MemoryItem | None:
        """获取单条记忆 - 需要遍历所有bot目录"""
        # 简单实现：遍历所有bot目录
        for bot_dir in self.storage_path.iterdir():
            if not bot_dir.is_dir():
                continue
            memory_file = bot_dir / f"{memory_id}.json"
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return MemoryItem(
                    id=data["id"],
                    content=data["content"],
                    metadata=data.get("metadata", {}),
                )
        return None
    
    async def update(self, request: UpdateMemoryRequest) -> MemoryItem:
        """更新记忆"""
        memory = await self.get(request.memory_id)
        if not memory:
            raise ValueError(f"Memory {request.memory_id} not found")
        
        new_content = request.content or memory.content
        new_metadata = request.metadata or memory.metadata
        
        # 找到并更新文件
        for bot_dir in self.storage_path.iterdir():
            if not bot_dir.is_dir():
                continue
            memory_file = bot_dir / f"{request.memory_id}.json"
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                data["content"] = new_content
                data["metadata"] = new_metadata
                data["updated_at"] = datetime.now().isoformat()
                
                with open(memory_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 重建索引（简化处理：删除旧的，添加新的向量）
                await self._rebuild_bot_index(bot_dir.name)
                
                return MemoryItem(
                    id=request.memory_id,
                    content=new_content,
                    metadata=new_metadata,
                )
        
        raise ValueError(f"Memory {request.memory_id} not found")
    
    async def _rebuild_bot_index(self, bot_id: str):
        """重建bot的记忆索引"""
        bot_dir = self._get_bot_dir(bot_id)
        memories = []
        vectors = []
        
        for memory_file in bot_dir.glob("*.json"):
            if memory_file.name == "index.json":
                continue
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                memories.append({
                    "id": data["id"],
                    "content": data["content"],
                    "created_at": data["created_at"],
                })
                
                vector = await self._embed_text(data["content"])
                if vector is not None:
                    vectors.append(vector.tolist())
        
        index = {"memories": memories, "vectors": vectors}
        self._save_index(bot_id, index)
    
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = await self.get(memory_id)
        if not memory:
            return False
        
        # 删除文件
        for bot_dir in self.storage_path.iterdir():
            if not bot_dir.is_dir():
                continue
            memory_file = bot_dir / f"{memory_id}.json"
            if memory_file.exists():
                memory_file.unlink()
                # 重建索引
                await self._rebuild_bot_index(bot_dir.name)
                return True
        
        return False
    
    async def get_all(self, bot_id: str, limit: int = 100) -> MemorySearchResult:
        """获取所有记忆"""
        bot_dir = self._get_bot_dir(bot_id)
        items = []
        
        for memory_file in sorted(bot_dir.glob("*.json"), reverse=True)[:limit]:
            if memory_file.name == "index.json":
                continue
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                items.append(MemoryItem(
                    id=data["id"],
                    content=data["content"],
                    metadata=data.get("metadata", {}),
                ))
        
        return MemorySearchResult(
            items=items,
            total=len(items),
            query=f"all_{bot_id}",
        )
    
    async def delete_all(self, bot_id: str) -> int:
        """删除所有记忆"""
        bot_dir = self._get_bot_dir(bot_id)
        count = 0
        
        for memory_file in bot_dir.glob("*.json"):
            if memory_file.name == "index.json":
                continue
            memory_file.unlink()
            count += 1
        
        # 删除索引
        index_file = bot_dir / "index.json"
        if index_file.exists():
            index_file.unlink()
        
        return count
    
    async def health_check(self) -> bool:
        """健康检查"""
        return self.storage_path.exists()