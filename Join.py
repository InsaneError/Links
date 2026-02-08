from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon import events
from asyncio import sleep
from .. import loader, utils
import re
import logging

logger = logging.getLogger(__name__)

@loader.tds
class SheoJoin(loader.Module):
    """Вступление в чаты/каналы по ссылкам. Создатель @SheoMod"""
    strings = {'name': 'SheoJoiner'}
    
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
            if url.startswith('@'):
                url = f"https://t.me/{url[1:]}"
            
            if 't.me/' in url:
                link_part = url.split('t.me/')[-1].split('/')[0]
                
                if link_part.startswith('+') or len(link_part) > 20:
                    # Приватный инвайт
                    await self.client(ImportChatInviteRequest(
                        hash=link_part[1:] if link_part.startswith('+') else link_part
                    ))
                    await message.delete()
                    return
                else:
                    # Публичный чат/канал
                    entity = await self.client.get_entity(link_part)
                    await self.client(JoinChannelRequest(entity))
                    await message.delete()
                    return
            
            await utils.answer(message, "Неверный формат ссылки")
            
        except Exception as e:
            logger.error(f"Join error: {e}")
            await utils.answer(message, f"Ошибка: {str(e)[:100]}")
