"""
Channel Adapter Abstract Interface
参考 Memoh: internal/channel/adapter. go
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import json
 
# =================== 类型定义 ===================
 
class ChannelType(str, Enum):
    """渠道类型"""
    LOCAL = "local"      # Web UI 内置
    TELEGRAM = "telegram"
    DISCORD = "discord"
    FEISHU = "feishu"
    EMAIL = "email"
    QQ = "qq"
    WECHAT = "wechat"
    WECOM = "wecom"
    MATRIX = "matrix"
 
 
class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    BUTTON = "button"
    CARDS = "cards"
 
 
@dataclass
class User:
    """用户"""
    id: str
    name: str = ""
    avatar: str = ""
    platform: str = ""  # 平台来源
    metadata: dict = field(default_factory=dict)
 
 
@dataclass
class Message:
    """消息"""
    id: str
    channel: str  # 渠道类型
    user: User
    content: str
    message_type: MessageType = MessageType.TEXT
    attachments: list[dict] = field(default_factory=list)
    reply_to: str = ""  # 回复的消息ID
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "user": {
                "id": self.user.id,
                "name": self.user.name,
            },
            "content": self.content,
            "type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
        }
 
 
@dataclass
class OutgoingMessage:
    """发送消息"""
    content: str
    message_type: MessageType = MessageType.TEXT
    attachments: list[dict] = field(default_factory=list)
    buttons: list[dict] = field(default_factory=list)  # [{"label": "xxx", "action": "xxx"}]
    cards: list[dict] = field(default_factory=list)    # 富文本卡片
    reply_to: str = ""
 
 
@dataclass
class ChannelConfig:
    """渠道配置"""
    channel_type: ChannelType
    enabled: bool = True
    bot_token: str = ""           # Bot Token
    bot_secret: str = ""          # Bot Secret (用于验证)
    api_key: str = ""             # API Key
    api_secret: str = ""          # API Secret
    webhook_url: str = ""         # Webhook URL
    # 特定配置
    allowed_users: list[str] = field(default_factory=list)  # 白名单用户
    allowed_groups: list[str] = field(default_factory=list) # 白名单群组
    forward_to: str = ""          # 转发到其他渠道
 
# =================== Adapter 接口 ===================
 
class ChannelAdapter(ABC):
    """渠道适配器抽象基类"""
    
    @property
    @abstractmethod
    def channel_type(self) -> ChannelType:
        """渠道类型"""
        pass
    
    @abstractmethod
    async def initialize(self, config: ChannelConfig) -> bool:
        """
        初始化渠道
        返回: 是否成功
        """
        pass
    
    @abstractmethod
    async def send_message(self, user_id: str, message: OutgoingMessage) -> str | None:
        """
        发送消息
        返回: 消息ID 或 None
        """
        pass
    
    @abstractmethod
    async def send_message_by_conversation(self, conversation_id: str, message: OutgoingMessage) -> str | None:
        """
        按会话ID发送消息（群聊等）
        """
        pass
    
    @abstractmethod
    async def handle_webhook(self, payload: dict) -> Message | None:
        """
        处理 Webhook 回调
        返回: 解析后的 Message 或 None
        """
        pass
    
    @abstractmethod
    async def close(self):
        """关闭连接"""
        pass
    
    # =================== 可选功能 ===================
    
    async def get_user_info(self, user_id: str) -> User | None:
        """获取用户信息（可选）"""
        return None
    
    async def list_chats(self) -> list[dict]:
        """列出可用会话（可选）"""
        return []
    
    def supports_buttons(self) -> bool:
        """是否支持按钮"""
        return False
    
    def supports_cards(self) -> bool:
        """是否支持富文本卡片"""
        return False
    
    def supports_inline_buttons(self) -> bool:
        """是否支持内联按钮"""
        return False
 
 
class ChannelAdapterFactory:
    """渠道适配器工厂"""
    
    _adapters: dict[ChannelType, type[ChannelAdapter]] = {}
    
    @classmethod
    def register(cls, channel_type: ChannelType, adapter_class: type[ChannelAdapter]):
        cls._adapters[channel_type] = adapter_class
    
    @classmethod
    def create(cls, channel_type: ChannelType, config: ChannelConfig) -> ChannelAdapter:
        if channel_type not in cls._adapters:
            raise ValueError(f"Unsupported channel: {channel_type}")
        return cls._adapters[channel_type](config)
    
    @classmethod
    def get_supported_channels(cls) -> list[ChannelType]:
        return list(cls._adapters.keys())


# =================== 统一消息管理器 ===================
 
class MessageDispatcher:
    """
    消息分发器
    统一管理多个渠道，处理消息收发
    """
    
    def __init__(self):
        self._adapters: dict[ChannelType, ChannelAdapter] = {}
        self._handlers: list[Callable[[Message], Any]] = []
    
    def register_handler(self, handler: Callable[[Message], Any]):
        """注册消息处理器"""
        self._handlers.append(handler)
    
    async def register_channel(self, config: ChannelConfig) -> ChannelAdapter:
        """注册渠道"""
        adapter = ChannelAdapterFactory.create(config.channel_type, config)
        await adapter.initialize(config)
        self._adapters[config.channel_type] = adapter
        return adapter
    
    async def unregister_channel(self, channel_type: ChannelType):
        """注销渠道"""
        if channel_type in self._adapters:
            await self._adapters[channel_type].close()
            del self._adapters[channel_type]
    
    async def dispatch_message(self, message: Message):
        """分发消息到处理器"""
        for handler in self._handlers:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Handler error: {e}")
    
    async def send_to_channel(
        self,
        channel_type: ChannelType,
        user_id: str,
        message: OutgoingMessage,
    ) -> str | None:
        """发送消息到指定渠道"""
        if channel_type not in self._adapters:
            return None
        return await self._adapters[channel_type].send_message(user_id, message)
    
    def get_channel_status(self) -> list[dict]:
        """获取渠道状态"""
        status = []
        for channel_type, adapter in self._adapters.items():
            status.append({
                "type": channel_type.value,
                "enabled": True,
                "supports_buttons": adapter.supports_buttons(),
                "supports_cards": adapter.supports_cards(),
            })
        return status


import asyncio
from .telegram_adapter import TelegramAdapter
from .discord_adapter import DiscordAdapter
from .feishu_adapter import FeishuAdapter
from .email_adapter import EmailAdapter
from .local_adapter import LocalAdapter
 
# 注册内置适配器
ChannelAdapterFactory.register(ChannelType.TELEGRAM, TelegramAdapter)
ChannelAdapterFactory.register(ChannelType.DISCORD, DiscordAdapter)
ChannelAdapterFactory.register(ChannelType.FEISHU, FeishuAdapter)
ChannelAdapterFactory.register(ChannelType.EMAIL, EmailAdapter)
ChannelAdapterFactory.register(ChannelType.LOCAL, LocalAdapter)