from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel, ChatInviteAlready
from asyncio import sleep
from .. import loader, utils

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
        
        url = args.strip()
        
        try:
            # 1. Если это юзернейм с @ - всегда публичный канал
            if url.startswith('@'):
                entity = await self.client.get_entity(url)
                await self.client(JoinChannelRequest(entity))
                await message.delete()
                return
            
            # 2. Обработка ссылок t.me
            if 't.me/' in url:
                # Получаем часть после t.me/
                url_part = url.split('t.me/')[1]
                # Берем первый сегмент (до слеша или до ?)
                identifier = url_part.split('/')[0].split('?')[0]
                
                # Определяем тип ссылки
                # Приватные инвайты: t.me/+ABC123 или t.me/joinchat/ABC123
                # Длинные хэши (>15 символов) - тоже приватные
                is_private = False
                
                if identifier.startswith('+'):
                    # Формат t.me/+ABC123
                    is_private = True
                    invite_hash = identifier[1:]
                elif url_part.startswith('joinchat/'):
                    # Формат t.me/joinchat/ABC123
                    is_private = True
                    invite_hash = url_part.split('joinchat/')[1].split('/')[0].split('?')[0]
                elif len(identifier) > 15:
                    # Длинный хэш - скорее всего приватный
                    is_private = True
                    invite_hash = identifier
                else:
                    # Короткий идентификатор - публичный канал
                    is_private = False
                    channel_id = identifier
            
                if is_private:
                    # Вступление в приватный чат
                    try:
                        result = await self.client(ImportChatInviteRequest(hash=invite_hash))
                        await message.delete()
                        return
                    except Exception as e:
                        error_str = str(e)
                        if "already" in error_str.lower():
                            await message.delete()  # Уже в чате
                            return
                        elif "hash" in error_str.lower():
                            await utils.answer(message, "❌ Неверный или устаревший инвайт")
                            return
                        else:
                            raise e
                else:
                    # Вступление в публичный канал
                    try:
                        entity = await self.client.get_entity(channel_id)
                        await self.client(JoinChannelRequest(channel=entity))
                        await message.delete()
                        return
                    except Exception as e:
                        error_str = str(e)
                        if "already" in error_str.lower():
                            await message.delete()  # Уже в канале
                            return
                        else:
                            raise e
            
            # 3. Если не распознали формат
            await utils.answer(message, "❌ Неверный формат ссылки. Используйте:\n@username\nhttps://t.me/channel\nt.me/+invite_hash")
            
        except Exception as e:
            error_msg = str(e)
            
            # Обработка частых ошибок
            if "USERNAME_NOT_OCCUPIED" in error_msg or "No user has" in error_msg:
                await utils.answer(message, "❌ Канал/пользователь не найден")
            elif "CHANNEL_PRIVATE" in error_msg:
                await utils.answer(message, "❌ Канал приватный, нужна инвайт-ссылка")
            elif "FLOOD_WAIT" in error_msg:
                await utils.answer(message, "⏳ Слишком много запросов, подождите")
            elif "already" in error_msg.lower():
                await message.delete()  # Тихий выход если уже в чате
            else:
                # Выводим чистую ошибку для отладки
                clean_error = error_msg.split('(')[0].strip()
                await utils.answer(message, f"❌ Ошибка: {clean_error[:80]}")
