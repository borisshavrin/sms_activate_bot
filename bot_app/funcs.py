import asyncio


async def edit_message(message, timer):
    for seconds_left in range(timer, 0, -1):
        await asyncio.sleep(1)
        await message.edit_text(f'Ожидание смс: {seconds_left}')

        if seconds_left == 1:
            await message.delete()


async def delete_message(message):
    await message.delete()
