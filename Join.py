from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import InputChannel, InputPeerChannel
from asyncio import sleep
from .. import loader, utils
import re
import logging

logger = logging.getLogger(__name__)

@loader.tds
class ChatJoinMod(loader.Module):
    """Вступление в чаты/каналы по ссылкам"""
    strings = {'name': 'ChatJoiner'}
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
    
    @loader.command()
    async def join(self, message):
        """<ссылка> - Вступить в чат/канал по ссылке"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "Укажите ссылку на чат/канал")
            return
        
        try:
            url = args.strip()
            
            # Обработка разных форматов ссылок
            if url.startswith('@'):
                username = url[1:]
            elif 't.me/' in url:
                username = url.split('t.me/')[-1].split('/')[0].split('?')[0]
            else:
                username = url
            
            # Убираем + для приватных инвайтов
            if username.startswith('+'):
                username = username[1:]
            
            # Пробуем разные методы вступления
            try:
                # Сначала пробуем как публичный канал/чат
                entity = await self.client.get_entity(username)
                
                if hasattr(entity, 'broadcast') or hasattr(entity, 'megagroup'):
                    # Это канал или супергруппа
                    await self.client(JoinChannelRequest(entity))
                else:
                    # Это обычный чат или что-то еще
                    await self.client(JoinChannelRequest(entity))
                
                await message.delete()
                return
                
            except ValueError as e:
                # Если не найден как entity, пробуем как приватный инвайт
                if "Cannot find any entity" in str(e) or "No user has" in str(e):
                    try:
                        # Пробуем как приватный инвайт
                        await self.client(ImportChatInviteRequest(hash=username))
                        await message.delete()
                        return
                    except Exception as invite_e:
                        logger.error(f"Private invite error: {invite_e}")
                        raise invite_e
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"Join error: {e}")
            error_msg = str(e)
            if "username is not registered" in error_msg.lower():
                await utils.answer(message, "Пользователь/чат не найден")
            elif "invite hash" in error_msg.lower():
                await utils.answer(message, "Неверная инвайт-ссылка")
            elif "already" in error_msg.lower():
                await message.delete()  # Уже состоим, просто удаляем сообщение
            else:
                await utils.answer(message, f"Ошибка: {error_msg[:100]}")
