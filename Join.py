from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from asyncio import sleep
from .. import loader, utils

@loader.tds
class ChatJoinMod(loader.Module):
    """Вступление в чаты/каналы по ссылкам"""
    strings = {'name': 'ChatJoiner'}
    
    async def client_ready(self, client, db):
        self.client = client
    
    @loader.command()
    async def join(self, message):
        """<ссылка> - Вступить в чат/канал по ссылке"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Укажите ссылку")
            return
        
        try:
            url = args.strip()
            
            # Если это юзернейм с @
            if url.startswith('@'):
                entity = await self.client.get_entity(url)
                await self.client(JoinChannelRequest(entity))
                await message.delete()
                return
            
            # Если это ссылка t.me
            if 't.me/' in url:
                # Извлекаем часть после t.me/
                part = url.split('t.me/')[1].split('?')[0].split('/')[0]
                
                # Если это приватный инвайт (начинается с + или длинный хеш)
                if part.startswith('+') or len(part) > 20:
                    hash_part = part[1:] if part.startswith('+') else part
                    await self.client(ImportChatInviteRequest(hash=hash_part))
                    await message.delete()
                    return
                else:
                    # Публичный чат/канал
                    entity = await self.client.get_entity(part)
                    await self.client(JoinChannelRequest(entity))
                    await message.delete()
                    return
            
            # Если это просто текст (пробуем как юзернейм)
            try:
                entity = await self.client.get_entity(url)
                await self.client(JoinChannelRequest(entity))
                await message.delete()
                return
            except:
                pass
            
            await utils.answer(message, "❌ Неверная ссылка")
            
        except Exception as e:
            error = str(e)
            if "already" in error.lower():
                await message.delete()  # Уже в чате - тихо удаляем
            elif "USERNAME_NOT_OCCUPIED" in error or "не найден" in error.lower():
                await utils.answer(message, "❌ Чат не найден")
            else:
                await utils.answer(message, f"❌ {error[:50]}")
