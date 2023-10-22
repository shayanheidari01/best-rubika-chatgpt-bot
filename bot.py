from rubpy import Client, handlers
from rubpy.structs import Struct
from typing import NoReturn, Literal
from httpx import AsyncClient, ReadTimeout
from asyncio import run, create_task, sleep as aiosleep

# Initialize an empty list to store responses
response_queue: list = []
http_client = AsyncClient()

# List of group IDs to filter messages from
groups = []

async def message_updates_model(message: Struct, result) -> (Literal[True] | None):
    # Custom model to handle message updates for User messages
    if message.action == 'New' and message.type == 'User':
        return True
    return None

async def message_updates_group_model(message: Struct, result) -> (Literal[True] | None):
    # Custom model to handle message updates for Group messages in specified groups
    if message.action == 'New' and message.type == 'Group' and message.object_guid in groups:
        return True
    return None

async def chooser() -> NoReturn:
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
    headers = {
        'Host': 'us-central1-chat-for-chatgpt.cloudfunctions.net',
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'User-Agent': 'com.tappz.aichat/1.2.2 iPhone/16.3.1 hw/iPhone12_5',
        'Accept-Language': 'en',
        'Content-Type': 'application/json; charset=UTF-8',
    }
    endpoint = 'https://us-central1-chat-for-chatgpt.cloudfunctions.net/basicUserRequestBeta'

    data = {
        'data': {
            'message': text,
        },
    }

    for trying in range(3):
        try:
            response = await http.post(endpoint, json=data, headers=headers)
            response_data = response.json()
            return response_data['result']['choices'][0]['text']
        except (TimeoutError, ReadTimeout):
            continue

    return 'خطا در دریافت پاسخ!'

async def reply_to_user(client: Client, object_guid: str, text: str, message_id: str):
    # Generate a ChatGPT response and send it as a reply to the user
    chatgpt_response = await send_chatgpt_request(http_client, text)
    if isinstance(chatgpt_response, str):
        chatgpt_response += '\n\n**توجه: به دلیل شلوغ بودن ربات برای پاسخ به شما، شما را صف نگه می‌دارد!**\n\n**لطفا جهت حمایت ما در کانال های زیر عضو شوید:**\n@shython\n@SiSiGIFS\n**گروه ما:**\nhttps://rubika.ir/joing/EBCIHEDF0CXPIXETEMOLSMUCOUCBBKIA'
        try:
            return await client.send_message(object_guid, '**● پاسخ چت‌جی‌پی‌تی:**\n' + chatgpt_response, message_id)
        except:
            return await client.send_message(object_guid, '**● پاسخ چت‌جی‌پی‌تی:**\nخطایی رخ داد!')

async def handler_message_updates(client: Client, update: Struct):
    object_guid: str = update.object_guid
    message_id: str = update.message_id
    text: str = update.raw_text

    if isinstance(text, str):
        response_queue.append(reply_to_user(client, object_guid, text, message_id))

async def handler_message_group_updates(client: Client, update: Struct):
    object_guid: str = update.object_guid
    message_id: str = update.message_id
    text: str = update.raw_text

    if isinstance(text, str):
        if text.startswith('//'):
            response_queue.append(reply_to_user(client, object_guid, text[2:].strip(), message_id))

async def main() -> NoReturn:
    create_task(chooser())

    async with Client('bot') as client:
        @client.on(handlers.MessageUpdates(message_updates_model))
        async def updates(update: Struct) -> NoReturn:
            create_task(handler_message_updates(client, update))

        @client.on(handlers.MessageUpdates(message_updates_group_model))
        async def updates(update: Struct) -> NoReturn:
            create_task(handler_message_group_updates(client, update))

        await client.run_until_disconnected()

run(main())
