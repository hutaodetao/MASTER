"""  Discord Adapter """  import asyncio
import json
from datetime import datetime
from typing import Any
import aiohttp
from .adapter import (    ChannelAdapter, ChannelType, ChannelConfig,
    Message, User, OutgoingMessage, MessageType)  class DiscordAdapter(ChannelAdapter):    """Discord Bot 适配器"""    
    def __init__(self, config: ChannelConfig):        self.config = config        self.bot_token = config.bot_token or ""        self.api_url = "https://discord.com/api/v10"        self._session: aiohttp.ClientSession | None = None
        self._session_id = None        
    @property
    def channel_type(self) -> ChannelType:        return ChannelType.DISCORD    
    async def initialize(self, config: ChannelConfig) -> bool:        """初始化 Discord Bot"""
        self._session = aiohttp.ClientSession(
            headers={                "Authorization": f"Bot {self.bot_token}",
                "Content-Type": "application/json",
            }        )                # 验证 Bot 身份        try:            async with self._session.get(f"{self.api_url}/users/@me") as resp:                if resp.status == 200:                    self._bot_info = await resp.json()                    return True        except Exception as e:            print(f"Discord init error: {e}")        
        return False
    
    async def _api_request(self, method: str, endpoint: str, **kwargs) -> dict:        """Discord API 请求"""        url = f"{self.api_url}{endpoint}"
        async with self._session.request(method, url, **kwargs) as resp:            if resp.status == 204:                return {}            data = await resp.json()
            if resp.status >= 400:                raise Exception(f"Discord API error: {data}")            return data    
    def _parse_message(self, payload: dict) -> Message | None:        """解析 Discord 消息"""        if payload.get("t") != "MESSAGE_CREATE":            return None        
        data = payload.get("d", {})        
        author = data.get("author", {})        
        user = User(            id=author.get("id", ""),            name=author.get("username", ""),            avatar=author.get("avatar", ""),            platform="discord",        )                # 解析内容        content = data.get("content", "")        message_type = MessageType.TEXT        
        # 检查附件        if data.get("attachments"):            message_type = MessageType.IMAGE if data["attachments"][0].get("content_type", "").startswith("image") else MessageType.FILE
        
        return Message(            id=data.get("id", ""),            channel="discord",            user=user,            content=content,            message_type=message_type,            timestamp=datetime.now(),            metadata={                "channel_id": data.get("channel_id"),                "guild_id": data.get("guild_id"),            },        )    
    async def handle_webhook(self, payload: dict) -> Message | None:        """处理 Webhook"""        return self._parse_message(payload)    
    async def send_message(self, user_id: str, message: OutgoingMessage) -> str | None:        """发送消息（到 DM）"""        try:            # 先创建 DM            dm = await self._api_request("POST", "/users/@me/channels", json={"recipient_id": user_id})            channel_id = dm.get("id")                        result = await self._api_request(                "POST", f"/channels/{channel_id}/messages",                json={"content": message.content}            )            return result.get("id")        except Exception as e:            print(f"Discord send error: {e}")            return None    
    async def send_message_by_conversation(self, conversation_id: str, message: OutgoingMessage) -> str | None:        """发送消息到频道"""        try:            result = await self._api_request(                "POST", f"/channels/{conversation_id}/messages",                json={"content": message.content}            )            return result.get("id")        except Exception as e:            print(f"Discord send error: {e}")            return None    
    async def send_embed(self, channel_id: str, embed: dict) -> str | None:        """发送 Embed 消息"""        try:            result = await self._api_request(                "POST", f"/channels/{channel_id}/messages",                json={"embeds": [embed]}            )            return result.get("id")        except Exception as e:            print(f"Discord embed error: {e}")            return None    
    def supports_cards(self) -> bool:        return True    
    async def close(self):        if self._session:            await self._session.close()