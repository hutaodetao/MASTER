"""
记忆抽取器 - 从任务结果中自动抽取关键事实
使用 LLM 进行智能抽取
"""
from dataclasses import dataclass
from typing import Any
import json
 
 
@dataclass
class ExtractedFacts:  # 抽取的关键事实
    facts: list[str]
    entities: list[dict]  # 实体：{"type": "person|organization|location", "name": "..."}
    summary: str
    tags: list[str]
 
 
class MemoryExtractor:
    """使用 LLM 从任务结果中抽取关键记忆"""
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM 客户端（需支持 chat 接口）
        """
        self.llm_client = llm_client
    
    async def extract(  # 抽取方法
        self,
        task_result: str,
        task_description: str = "",
    ) -> ExtractedFacts:
        """
        从任务结果中抽取关键事实
        
        Args:
            task_result: 任务执行结果
            task_description: 任务描述（可选）
            
        Returns:
            ExtractedFacts: 包含事实、实体、摘要、标签
        """
        # 构建抽取 prompt
        prompt = self._build_extraction_prompt(task_result, task_description)
        
        if self.llm_client is None:
            # 无 LLM 时的简单回退
            return self._simple_extraction(task_result)
        
        # 调用 LLM 抽取
        try:
            response = await self._call_llm(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            # LLM 调用失败，回退到简单抽取
            return self._simple_extraction(task_result)
    
    def _build_extraction_prompt(self, task_result: str, task_description: str) -> str:
        """构建抽取提示"""
        return f"""你是一个记忆抽取专家。从以下任务结果中抽取关键信息，生成结构化的记忆条目。

任务描述：{task_description or "未知任务"}

任务结果：
{task_result}

请从结果中抽取：
1. 关键事实（最重要的信息点，2-5条）
2. 实体（人名、组织、地点等）
3. 一句话摘要（描述这个任务完成了什么）
4. 标签（3-5个关键词，用逗号分隔）

请以 JSON 格式输出：
{{
    "facts": ["事实1", "事实2", ...],
    "entities": [{{"type": "person|organization|location", "name": "名称"}}, ...],
    "summary": "一句话摘要",
    "tags": ["标签1", "标签2", ...]
}}

只输出 JSON，不要其他内容。"""    
    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        # 适配不同的 LLM 客户端
        if hasattr(self.llm_client, 'chat'):  # OpenAI 风格
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        elif hasattr(self.llm_client, 'complete'):  # Anthropic 风格
            response = await self.llm_client.complete(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3,
            )
            return response.get("completion", "{}")
        
        # 默认：返回空
        return "{}"
    
    def _parse_llm_response(self, response: str) -> ExtractedFacts:  # 解析 LLM 响应
        """解析 LLM 返回的 JSON"""
        try:
            # 提取 JSON 部分
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return ExtractedFacts(
                    facts=data.get("facts", []),
                    entities=data.get("entities", []),
                    summary=data.get("summary", ""),
                    tags=data.get("tags", []),
                )
        except (json.JSONDecodeError, KeyError):
            pass
        
        # 解析失败，回退
        return self._simple_extraction(response)
    
    def _simple_extraction(self, text: str) -> ExtractedFacts:  # 简单抽取（无 LLM 时使用）
        """简单的规则-based 抽取"""
        # 提取句子作为事实
        sentences = text.replace("。", "\n").replace("！", "\n").replace("？", "\n").split("\n")
        facts = [s.strip() for s in sentences if len(s.strip()) > 10][:5]
        
        # 简单标签提取（高频词）
        words = text.split()
        word_freq = {}
        for word in words:
            if len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        tags = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
        
        return ExtractedFacts(
            facts=facts,
            entities=[],
            summary=text[:100] + "..." if len(text) > 100 else text,
            tags=tags,
        )
    
    async def should_remember(  # 判断是否需要记忆
        self,
        task_result: str,
        threshold: float = 0.5,
    ) -> bool:
        """
        判断任务结果是否值得记忆
        
        Args:
            task_result: 任务结果
            threshold: 阈值
            
        Returns:
            bool: 是否应该记住
        """
        if not task_result or len(task_result.strip()) < 20:
            return False
        
        # 简单规则：
        # 1. 结果长度适中（不太短也不太长）
        # 2. 包含有意义的内容
        
        length = len(task_result)
        if length < 50 or length > 50000:
            return False
        
        # 尝试抽取
        facts = await self.extract(task_result)
        
        # 如果能抽取到事实，或者有摘要，则记住
        return len(facts.facts) > 0 or len(facts.summary) > 10


class BatchMemoryExtractor:
    """批量记忆抽取器"""
    
    def __init__(self, extractor: MemoryExtractor, batch_size: int = 5):
        self.extractor = extractor
        self.batch_size = batch_size
    
    async def extract_batch(  # 批量抽取
        self,
        task_results: list[dict],  # list of {"description": "...", "result": "..."}
    ) -> list[ExtractedFacts]:
        """
        批量抽取记忆
        
        Args:
            task_results: 任务结果列表
            
        Returns:
            list[ExtractedFacts]: 每个任务的抽取结果
        """
        results = []
        
        for task in task_results:
            result = await self.extractor.extract(
                task_result=task.get("result", ""),
                task_description=task.get("description", ""),
            )
            results.append(result)
        
        return results