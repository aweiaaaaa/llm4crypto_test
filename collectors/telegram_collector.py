import asyncio
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set

from telethon import TelegramClient, events, types
from telethon.errors import SessionPasswordNeededError, ApiIdInvalidError, AuthKeyError
from telethon.sessions import StringSession

from configs.config import Config
from utils.helpers import save_to_json, random_delay, logger

class TelegramCollector:
    def __init__(self):
        self.api_id = Config.TELEGRAM_API_ID
        self.api_hash = Config.TELEGRAM_API_HASH
        self.phone = Config.TELEGRAM_PHONE
        self.client = None
        self.channels = Config.TELEGRAM_CHANNELS
        self.messages: List[Dict[str, Any]] = []
        self.seen_message_ids: Set[int] = set()
        self.request_delay = Config.REQUEST_DELAY

    async def _init_client(self):
        try:
            api_id_int = int(self.api_id) if self.api_id else None
        except (ValueError, TypeError):
            api_id_int = None
            
        if not api_id_int or not self.api_hash:
            logger.warning("Telegram API credentials not configured, skipping Telegram collection")
            raise ValueError("Telegram API credentials not configured")
        
        try:
            self.client = TelegramClient(
                'telegram_session', 
                api_id_int, 
                self.api_hash,
                connection_retries=3,
                timeout=30
            )
            await self.client.start(self.phone)
            
            if not await self.client.is_user_authorized():
                raise SessionPasswordNeededError("Telegram client not authorized")
            
            logger.info("Telegram client initialized successfully")
        except ApiIdInvalidError:
            logger.error("Invalid Telegram API ID or Hash")
            raise
        except AuthKeyError:
            logger.error("Invalid Telegram authorization key")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            raise

    async def _resolve_entity(self, channel_name: str):
        try:
            return await self.client.get_entity(channel_name)
        except Exception as e:
            logger.warning(f"Could not resolve entity {channel_name}: {e}")
            return None

    async def _get_channel_messages(self, channel_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        entity = await self._resolve_entity(channel_name)
        if not entity:
            return []

        channel_messages = []
        try:
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.id in self.seen_message_ids:
                    continue
                
                self.seen_message_ids.add(message.id)
                
                media_info = {}
                if message.media:
                    if isinstance(message.media, types.MessageMediaPhoto):
                        media_info['type'] = 'photo'
                    elif isinstance(message.media, types.MessageMediaDocument):
                        media_info['type'] = 'document'
                    elif isinstance(message.media, types.MessageMediaVideo):
                        media_info['type'] = 'video'
                    elif isinstance(message.media, types.MessageMediaWebPage):
                        media_info['type'] = 'webpage'
                
                sender_name = None
                if message.sender_id:
                    try:
                        sender = await self.client.get_entity(message.sender_id)
                        sender_name = sender.first_name if hasattr(sender, 'first_name') else None
                    except Exception:
                        sender_name = None
                
                channel_messages.append({
                    'message_id': message.id,
                    'channel_name': channel_name,
                    'sender_id': message.sender_id,
                    'sender_name': sender_name,
                    'text': message.text,
                    'date': message.date.isoformat(),
                    'views': message.views or 0,
                    'forwards': message.forwards or 0,
                    'replies': message.replies.replies if message.replies else 0,
                    'media_info': media_info,
                    'reply_to_msg_id': message.reply_to_msg_id,
                    'data_source': 'telegram',
                    'scraped_at': datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            logger.error(f"Error fetching messages from {channel_name}: {e}")
        
        logger.info(f"Fetched {len(channel_messages)} messages from {channel_name}")
        return channel_messages

    async def collect_channel_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.client:
            await self._init_client()
        
        all_messages = []
        for channel in self.channels:
            try:
                messages = await self._get_channel_messages(channel, limit)
                all_messages.extend(messages)
                await random_delay(self.request_delay, self.request_delay * 2)
            except Exception as e:
                logger.error(f"Error collecting from channel {channel}: {e}")
        
        return all_messages

    async def start_realtime_listener(self, callback=None):
        if not self.client:
            await self._init_client()

        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            message = event.message
            if message.id in self.seen_message_ids:
                return
            
            self.seen_message_ids.add(message.id)
            
            media_info = {}
            if message.media:
                if isinstance(message.media, types.MessageMediaPhoto):
                    media_info['type'] = 'photo'
                elif isinstance(message.media, types.MessageMediaDocument):
                    media_info['type'] = 'document'
                elif isinstance(message.media, types.MessageMediaVideo):
                    media_info['type'] = 'video'
            
            msg_data = {
                'message_id': message.id,
                'channel_name': str(event.chat_id),
                'sender_id': message.sender_id,
                'sender_name': (await self.client.get_entity(message.sender_id)).first_name if message.sender_id else None,
                'text': message.text,
                'date': message.date.isoformat(),
                'views': message.views or 0,
                'forwards': message.forwards or 0,
                'media_info': media_info,
                'data_source': 'telegram',
                'scraped_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.messages.append(msg_data)
            
            if callback:
                await callback(msg_data)
            
            logger.info(f"New message from {event.chat_id}: {message.text[:50]}...")

        logger.info("Realtime listener started")
        await self.client.run_until_disconnected()

    async def collect_and_save(self, output_file: Optional[str] = None, limit: int = 50) -> None:
        messages = await self.collect_channel_history(limit)
        
        if not output_file:
            output_file = f"{Config.RAW_DATA_DIR}/telegram_messages_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        
        save_to_json(messages, output_file)
        logger.info(f"Telegram messages saved to {output_file}")

    def close(self):
        if self.client:
            asyncio.run(self.client.disconnect())

def run_telegram_collector():
    collector = TelegramCollector()
    try:
        asyncio.run(collector.collect_and_save())
    except Exception as e:
        logger.error(f"Telegram collection failed: {e}")
    finally:
        collector.close()

if __name__ == "__main__":
    run_telegram_collector()