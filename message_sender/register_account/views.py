import os
import threading
import asyncio
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime
import json     

phone_code_hashes = {}

os.makedirs('sessions', exist_ok=True)

def create_session(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        api_id = int(request.POST.get('api_id'))
        api_hash = request.POST.get('api_hash')

        # Start the code sending task in a thread
        def run_async_code():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(send_code(phone_number, api_id, api_hash))
            finally:
                loop.close()

        thread = threading.Thread(target=run_async_code)
        thread.start()

        # Redirect to enter_code with parameters
        return redirect(reverse('enter_code', kwargs={
            'phone_number': phone_number,
            'api_id': api_id,
            'api_hash': api_hash
        }))

    return render(request, 'register_account/create_session.html')

def enter_code(request, phone_number, api_id, api_hash):
    if request.method == 'POST':
        code = request.POST.get('code')
        password = request.POST.get('password', '')

        asyncio.run(handle_code_submission(phone_number, api_id, api_hash, code, password))

        account_data = {
            f"acc_{api_id}": {
                "api_id": api_id,
                "api_hash": api_hash,
                "time": datetime.now().isoformat(),
                "status": True
            }
        }
        try:
            file_path = "sessions/accounts.json"
            with open(file_path, "r") as file:
                data = json.load(file)

            data.update(account_data)

            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)

        except FileNotFoundError:
            data = {}

        return render(request, 'register_account/success.html', {'message': "Session created successfully!"})

    return render(request, 'register_account/enter_code.html', {
        'phone_code_hash': phone_code_hashes.get(phone_number, '')
    })


async def send_code(phone_number, api_id, api_hash):
    client = TelegramClient(f'sessions/acc_{api_id}', int(api_id), api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            sent_code = await client.send_code_request(phone_number)
            phone_code_hashes[phone_number] = sent_code.phone_code_hash

            print(f"Phone code hash for {phone_number}: {sent_code.phone_code_hash}")
    except Exception as e:
        print(f"An error occurred while sending code: {e}")
    finally:
        await client.disconnect()


async def handle_code_submission(phone_number, api_id, api_hash, code, password):
    client = TelegramClient(f'sessions/acc_{api_id}', int(api_id), api_hash)
    await client.connect()

    try:
        phone_code_hash = phone_code_hashes.get(phone_number)
        if not phone_code_hash:
            raise ValueError("Phone code hash not found. Please request a new code.")
        if not password:
            await client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
        else:
            await client.sign_in(phone_number, code, password=str(password), phone_code_hash=phone_code_hash)

        if await client.is_user_authorized():
            session = StringSession.save(client.session)

    except Exception as e:
        print(f"An error occurred while handling code submission: {e}")
    finally:
        await client.disconnect()
