"""  Channel System
多渠道消息适配器
参考 Memoh: internal/ channel/  """  from .adapter import (    ChannelAdapter,    ChannelAdapterFactory,    ChannelType,    ChannelConfig,    Message, User, OutgoingMessage,    MessageType,    MessageDispatcher,)  from .telegram_ adapter import TelegramAdapter
from .discord_adapter import DiscordAdapter
from .feishu_adapter import FeishuAdapter
from .email_adapter import EmailAdapter
from .local_adapter import LocalAdapter, WebMessageHandler  __all__ = [    # 核心接口    "ChannelAdapter",    "ChannelAdapterFactory",    "ChannelType",    "ChannelConfig",    "Message",    "User",    "OutgoingMessage",    "MessageType",    "MessageDispatcher",    # 适配器    "TelegramAdapter",    "DiscordAdapter",    "FeishuAdapter",    "EmailAdapter",    "LocalAdapter",    # Web 处理器    "WebMessageHandler",]