from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from asyncio import sleep
from .. import loader, utils
import re

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
            await utils.answer(message, "❌ Укажите ссылку")
            return
        
        try:
            url = args.strip()
            
            # 1. Определяем тип ссылки
            is_private_invite = False
            invite_hash = None
            channel_username = None
            
            # Проверяем, это публичная ссылка или приватный инвайт
            if 't.me/joinchat/' in url or 't.me/+' in url or 't.me/' in url and len(url.split('t.me/')[-1].split('/')[0]) > 20:
                is_private_invite = True
                # Извлекаем хэш из ссылки
                if 't.me/joinchat/' in url:
                    invite_hash = url.split('t.me/joinchat/')[-1].split('/')[0]
                elif 't.me/+' in url:
                    invite_hash = url.split('t.me/+')[-1].split('/')[0]
                elif 't.me/' in url:
                    invite_hash = url.split('t.me/')[-1].split('/')[0]
            else:
                # Публичная ссылка
                if url.startswith('@'):
                    channel_username = url[1:]
                elif 't.me/' in url:
                    channel_username = url.split('t.me/')[-1].split('/')[0].split('?')[0]
                else:
                    channel_username = url
            
            # 2. Используем правильный метод в зависимости от типа
            if is_private_invite and invite_hash:
                # Для приватных чатов используем ImportChatInviteRequest[citation:1][citation:7]
                await self.client(ImportChatInviteRequest(hash=invite_hash))
            elif channel_username:
                # Для публичных каналов используем JoinChannelRequest[citation:6][citation:7]
                entity = await self.client.get_entity(channel_username)
                await self.client(JoinChannelRequest(channel=entity))
            else:
                await utils.answer(message, "❌ Не удалось распознать ссылку")
                return
            
            # Успешно - удаляем команду
            await message.delete()
            
        except Exception as e:
            error_msg = str(e)
            # Обрабатываем распространённые ошибки
            if "already a participant" in error_msg.lower() or "Уже состою" in error_msg.lower():
                await message.delete()  # Тишина, если уже в чате
            elif "too many" in error_msg.lower():
                await utils.answer(message, "❌ Превышен лимит вступлений в чаты")
            elif "hash is invalid" in error_msg.lower():
                await utils.answer(message, "❌ Неверная или устаревшая инвайт-ссылка")
            elif "private" in error_msg.lower():
                await utils.answer(message, "❌ Это приватный канал, нужна инвайт-ссылка")
            else:
                await utils.answer(message, f"❌ Ошибка: {error_msg[:80]}")
