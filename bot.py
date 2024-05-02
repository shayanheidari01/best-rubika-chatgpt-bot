from rubpy import Client
from rubpy.types import Updates
from httpx import AsyncClient, ReadTimeout
from asyncio import create_task, sleep as aiosleep

# Initialize an empty list to store responses
response_queue: list = []
http_client = AsyncClient()

# List of group IDs to filter messages from
groups = []

async def message_updates_model(message: Updates, result):
    # Custom model to handle message updates for User messages
    return message.action == 'New' and message.type == 'User'

async def message_updates_group_model(message: Updates, result):
    # Custom model to handle message updates for Group messages in specified groups
    return message.action == 'New' and message.type == 'Group' and message.object_guid in groups

async def chooser():
    while True:
        await aiosleep(0.1)
        for queue in response_queue:
            response_queue.remove(queue)
            await aiosleep(5)

            try:
                await queue
            except Exception as exc:
                print(exc)

async def send_chatgpt_request(http: AsyncClient, text: str):
    # HTTP request to a ChatGPT service for text generation
    endpoint = 'https://chatgpt-api3.onrender.com'
    data = {'text': text}

    for trying in range(3):
        try:
            response = await http.post(endpoint, json=data)
            response_data = response.json()
            return response_data.get('message')
        except (TimeoutError, ReadTimeout):
            continue
        except Exception as exc:
            print('ERROR:', exc)

    return 'خطا در دریافت پاسخ!'

async def reply_to_user(client: Client, object_guid: str, text: str, message_id: str):
    # Generate a ChatGPT response and send it as a reply to the user
    chatgpt_response = await send_chatgpt_request(http_client, text)
    if isinstance(chatgpt_response, str):
        if object_guid[0] == 'g':
            return await client.send_message(object_guid, '**● پاسخ چت‌جی‌پی‌تی:**\n' + chatgpt_response, message_id)

        chatgpt_response += '\n\n**توجه: به دلیل شلوغ بودن ربات برای پاسخ به شما، شما را صف نگه می‌دارد!**\n\n**لطفا جهت حمایت ما در کانال های زیر عضو شوید:**\n@shython\n@SiSiGIFS\n**گروه ما:**\nhttps://rubika.ir/joing/EBCIHEDF0CXPIXETEMOLSMUCOUCBBKIA'
        try:
            return await client.send_message(object_guid, '**● پاسخ چت‌جی‌پی‌تی:**\n' + chatgpt_response, message_id)
        except:
            return await client.send_message(object_guid, '**● پاسخ چت‌جی‌پی‌تی:**\nخطایی رخ داد!')

async def handler_message_updates(client: Client, update: Updates):
    object_guid: str = update.object_guid
    message_id: str = update.message_id
    text: str = update.raw_text

    if isinstance(text, str):
        response_queue.append(reply_to_user(client, object_guid, text, message_id))

async def handler_message_group_updates(client: Client, update: Updates):
    object_guid: str = update.object_guid
    message_id: str = update.message_id
    text: str = update.raw_text

    if isinstance(text, str):
        if text.startswith('//'):
            response_queue.append(reply_to_user(client, object_guid, text[2:].strip(), message_id))

# async def main():
#     create_task(chooser())

bot = Client('bot')

@bot.on_message_updates(message_updates_model)
async def updates(update: Updates):
    if not hasattr(bot, 'maked_chooser'):
        create_task(chooser())
        bot.maked_chooser = True

    create_task(handler_message_updates(bot, update))

@bot.on_message_updates(message_updates_group_model)
async def updates(update: Updates):
    create_task(handler_message_group_updates(bot, update))

bot.run()
