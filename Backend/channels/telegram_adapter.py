"""
Telegram Adapter
""" 
import asyncio
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any
import aiohttp

from .adapter import (
    ChannelAdapter, ChannelType, ChannelConfig,
    Message, User, OutgoingMessage, MessageType
)


class TelegramAdapter(ChannelAdapter):
    """Telegram Bot 适配器"""
    
    def __init__(self, config: ChannelConfig):
        self.config = config
        self.bot_token = config.bot_api_key or ""
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._session: aiohttp.ClientSession | None = None
    
    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.TELEGRAM
    
    async def initialize(self, config: ChannelConfig) -> bool:
        """初始化 Telegram Bot"""
        self._session = aiohttp.ClientSession()
        
        # 获取 Bot 信息验证
        try:
            async with self._session.get(f"{self.api_url}/getMe") as resp:
                data = await resp.json()
                if data.get("ok"):
                    self._bot_info = data.get("result", {})
                    return True
        except Exception as e:
            print(f"Telegram init error: {e}")
        
        return False
    
    async def _api_request(self, method: str, **kwargs) -> dict:
        """Telegram API 请求"""
        url = f"{self.api_url}/{method}"
        async with self._session.post(url, json=kwargs) as resp:
            data = await resp.json()
            if not data.get("ok"):
                raise Exception(f"Telegram API error: {data.get('description')}")
            return data.get("result", {})
    
    def _parse_message(self, update: dict) -> Message | None:
        """解析 Telegram 更新"""
        if "message" not in update:
            return None
        
        msg = update["message"]
        from_user = msg.get("from", {})
        
        user = User(
            id=str(from_user.get("id", "")),
            name=f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
            avatar=from_user.get("photo", {}).get("small_file_id", ""),
            platform="telegram",
        )
        
        # 解析消息内容
        content = ""
        message_type = MessageType.TEXT
        
        if "text" in msg:
            content = msg["text"]
        elif "photo" in msg:
            content = msg["caption"] or "[图片]"
            message_type = MessageType.IMAGE
        elif "voice" in msg:
            content = "[语音消息]"
            message_type = MessageType.AUDIO
        elif "document" in msg:
            content = f"[文件: {msg['document'].get('file_name', 'unknown')}]"
            message_type = MessageType.FILE
        
        return Message(
            id=str(msg.get("message_id", "")),
            channel="telegram",
            user=user,
            content=content,
            message_type=message_type,
            timestamp=datetime.fromtimestamp(msg.get("date", 0)),
            metadata={"chat_id": msg.get("chat", {}).get("id")},
        )
    
    async def handle_webhook(self, payload: dict) -> Message | None:
        """处理 Webhook"""
        return self._parse_message(payload)
    
    async def send_message(self, user_id: str, message: OutgoingMessage) -> str | None:
        """发送消息"""
        try:
            result = await self._api_request(
                "sendMessage",
                chat_id=user_id,
                text=message.content,
                parse_mode="Markdown",
            )
            return str(result.get("message_id"))
        except Exception as e:
            print(f"Send error: {e}")
            return None
    
    async def send_message_by_conversation(self, conversation_id: str, message: OutgoingMessage) -> str | None:
        """发送消息到群组"""
        return await self.send_message(conversation_id, message)
    
    async def send_buttons(self, user_id: str, text: str, buttons: list[dict]) -> str | None:
        """发送带按钮的消息"""
        try:
            keyboard = {
                "inline_keyboard": [
                    [{"text": btn.get("label", ""), "callback_data": btn.get("action", "")} 
                     for btn in buttons]
                ]
            }
            
            result = await self._api_request(
                "sendMessage",
                chat_id=user_id,
                text=text,
                reply_markup=keyboard,
            )
            return str(result.get("message_id"))
        except Exception as e:
            print(f"Send buttons error: {e}")
            return None
    
    def supports_buttons(self) -> bool:
        return True
    
    def supports_inline_buttons(self) -> bool:
        return True
    
    async def close(self):
        if self._session:
            await self._session.close()


class TelegramWebhookVerifier:
    """Telegram Webhook 验证"""
    
    def __init__(self, bot_token: str, secret_token: str = None):
        self.bot_token = bot_token
        self.secret_token = secret_token
    
    def verify(self, headers: dict, body: bytes) -> bool:
        """验证请求是否来自 Telegram"""
        if self.secret_token:
            # 验证 X-Telegram-Bot-Api-Secret-Token
            secret = headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret != self.secret_token:
                return False
        
        return True
    
    def parse_update(self, body: bytes) -> dict:
        """解析更新"""
        return json.loads(body.decode())