"""
Feishu (飞书) Adapter
"""
import asyncio
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Any
import aiohttp

from .adapter import (
    ChannelAdapter, ChannelType, ChannelConfig,
    Message, User, OutgoingMessage, MessageType
)


class FeishuAdapter(ChannelAdapter):
    """飞书 Bot 适配器"""
    
    def __init__(self, config: ChannelConfig):
        self.config = config
        self.app_id = config.api_key or ""
        self.app_secret = config.api_secret or ""
        self.api_url = "https://open.feishu.cn/open-apis"
        self._session: aiohttp.ClientSession | None = None
        self._tenant_access_token = None
        self._token_expires_at = 0
    
    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.FEISHU
    
    async def initialize(self, config: ChannelConfig) -> bool:
        """初始化飞书 Bot"""
        self._session = aiohttp.ClientSession()
        
        # 获取 tenant_access_token
        try:
            await self._refresh_token()
            return True
        except Exception as e:
            print(f"Feishu init error: {e}")
        
        return False
    
    async def _refresh_token(self):
        """刷新 tenant_access_token"""
        url = f"{self.api_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        
        async with self._session.post(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                self._tenant_access_token = data.get("tenant_access_token")
                self._token_expires_at = time.time() + data.get("expire", 7200)
            else:
                raise Exception(f"Feishu token error: {data}")
    
    async def _api_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """飞书 API 请求"""
        # 检查 token 过期
        if time.time() >= self._token_expires_at:
            await self._refresh_token()
        
        url = f"{self.api_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json",
        }
        
        async with self._session.request(method, url, headers=headers, **kwargs) as resp:
            data = await resp.json()
            if data.get("code") != 0:
                raise Exception(f"Feishu API error: {data}")
            return data.get("data", {})
    
    @property
    def tenant_access_token(self) -> str:
        return self._tenant_access_token or ""
    
    def _parse_message(self, payload: dict) -> Message | None:
        """解析飞书消息"""
        # 验证签名
        if not self._verify_signature(payload):
            return None
        
        event_type = payload.get("type")
        if event_type == "url_verification":
            # 验证 URL
            return None
        
        if event_type != "im.message.message_v1":
            return None
        
        message_event = payload.get("event", {})
        message = message_event.get("message", {})
        
        user_id = message.get("sender_id", {}).get("user_id", "")
        
        user = User(
            id=user_id,
            name="",  # 需要额外调用获取
            platform="feishu",
        )
        
        # 解析消息内容
        content = json.loads(message.get("content", "{}"))
        msg_type = message.get("msg_type", "text")
        
        if msg_type == "text":
            text_content = content.get("text", "")
        elif msg_type == "image":
            text_content = "[图片]"
        elif msg_type == "file":
            text_content = f"[文件: {content.get('file_name', 'unknown')}]"
        else:
            text_content = str(content)
        
        return Message(
            id=message.get("message_id", ""),
            channel="feishu",
            user=user,
            content=text_content,
            message_type=MessageType.TEXT,
            timestamp=datetime.now(),
            metadata={
                "chat_id": message.get("chat_id"),
                "msg_type": msg_type,
            },
        )
    
    def _verify_signature(self, payload: dict) -> bool:
        """验证飞书签名"""
        timestamp = payload.get("timestamp", "")
        nonce = payload.get("nonce", "")
        signature = payload.get("signature", "")
        
        # 构建签名字符串
        sign_str = f"{timestamp}{nonce}{self.app_secret}"
        
        # 计算签名
        h = hashlib.sha256(sign_str.encode())
        expected_signature = base64.b64encode(h.digest()).decode()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_webhook(self, payload: dict) -> Message | None:
        """处理 Webhook"""
        return self._parse_message(payload)
    
    async def send_message(self, user_id: str, message: OutgoingMessage) -> str | None:
        """发送消息（给用户）"""
        try:
            # 先创建会话
            result = await self._api_request(
                "POST", "/im/v1/chats",
                json={
                    "user_id_list": [user_id],
                    "chat_type": "p2p",
                }
            )
            
            chat_id = result.get("chat", {}).get("chat_id")
            if not chat_id:
                return None
            
            # 发送消息
            return await self.send_message_by_conversation(chat_id, message)
        
        except Exception as e:
            print(f"Feishu send error: {e}")
            return None
    
    async def send_message_by_conversation(self, conversation_id: str, message: OutgoingMessage) -> str | None:
        """发送消息到会话"""
        try:
            msg_type = "text"
            content = json.dumps({"text": message.content})
            
            result = await self._api_request(
                "POST", f"/im/v1/chats/{conversation_id}/messages",
                json={
                    "msg_type": msg_type,
                    "content": content,
                }
            )
            
            return result.get("message_id")
        except Exception as e:
            print(f"Feishu send error: {e}")
            return None
    
    async def send_card(self, user_id: str, card_template: dict) -> str | None:
        """发送卡片消息"""
        try:
            # 创建会话
            result = await self._api_request(
                "POST", "/im/v1/chats",
                json={"user_id_list": [user_id], "chat_type": "p2p"}
            )
            
            chat_id = result.get("chat", {}).get("chat_id")
            if not chat_id:
                return None
            
            # 发送卡片
            result = await self._api_request(
                "POST", f"/im/v1/chats/{chat_id}/messages",
                json={
                    "msg_type": "interactive",
                    "card": json.dumps(card_template),
                }
            )
            
            return result.get("message_id")
        except Exception as e:
            print(f"Feishu card error: {e}")
            return None
    
    def supports_Buttons(self) -> bool:
        return True
    
    def supports_cards(self) -> bool:
        return True
    
    async def close(self):
        if self._session:
            await self._session.close()


class FeishuCardBuilder:
    """飞书卡片构建器"""
    
    @staticmethod
    def create_basic_card(content: str, buttons: list[dict] = None) -> dict:
        """创建基础卡片"""
        card = {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": "M. A. S. T. E. R."}},
            "elements": [
                {"tag": "markdown", "content": content}
            ]
        }
        
        if buttons:
            button_elements = []
            for btn in buttons:
                button_elements.append({
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": btn.get("label", "")},
                    "type": "primary" if btn.get("primary") else "default",
                    "action": {
                        "type": "open_url",
                        "data": {"url": btn.get("url", "")}
                    } if btn.get("url") else {
                        "type": "request",
                        "data": {"path": btn.get("action", "")}
                    }
                })
            
            card["elements"].append({
                "tag": "action",
                "actions": button_elements
            })
        
        return card