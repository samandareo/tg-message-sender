import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

from telethon import TelegramClient
import requests
from datetime import datetime
import asyncio
import json

async def send_message(client, name, username, message):
    try:
        message = message.replace('$name', name)
        await client.send_message(username, message)
        logging.info(f"Message sent to {name} ({username})")
    except Exception as e:
        logging.error(f"Failed to send message to {name} ({username}): {e}")

async def receive_data(data, message):
    # Import the stop_thread flag from views
    from sender.views import stop_thread

    with open('sessions/accounts.json', 'r') as file:
        accounts = json.load(file)

    account_status = 0
    total_sent_messages = 0
    for account_id, account_data in accounts.items():
        # Check if stop was requested
        if stop_thread:
            logging.info("Message sending stopped by user")
            break
            
        if account_data['status']:
            account_status += 1
            api_id = account_data['api_id']
            api_hash = account_data['api_hash']
            logging.info(f"Sending messages to {account_id}")
            client = TelegramClient(f'./sessions/acc_{api_id}', api_id, api_hash)
            await client.connect()
            message_count = 0
            for index, row in data.iterrows():
                # Check if stop was requested
                if stop_thread:
                    logging.info("Message sending stopped by user")
                    break
                    
                if message_count <= 100:
                    name = row['Name']
                    username = row['Username']
                    await send_message(client, name, username, message)
                    await asyncio.sleep(1/0.05)
                    total_sent_messages += 1
                    message_count += 1
                    data.drop(index, inplace=True)
                else:
                    try:
                        BOT_TOKEN = "7767200091:AAETCGDplMsJHad-6vzhzPp-yt2YdavCsCE"
                        CHAT_ID = "-1002213203187"
                        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        data_json = {"chat_id": CHAT_ID, "text": f"{account_id} sent: {message_count} messages"}
                        response = requests.post(url, json=data_json)
                        if response.status_code == 200:
                            logging.info(f"Message sent to {account_id}")
                        else:
                            logging.error(f"Failed to send message to {account_id}: {response.status_code}")
                    except Exception as e:
                        logging.error(f"Failed to send message to {account_id}: {e}")

                    await client.disconnect()
                    break
            await client.disconnect()
                
            accounts[account_id]['status'] = False
            accounts[account_id]['time'] = datetime.now().isoformat()

            if data.empty:
                break
        
        if account_status == 0:
            
            break

    with open('sessions/accounts.json', 'w') as file:
        json.dump(accounts, file, indent=4)

    BOT_TOKEN = "7767200091:AAETCGDplMsJHad-6vzhzPp-yt2YdavCsCE"
    CHAT_ID = "-1002213203187"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data_json = {"chat_id": CHAT_ID, "text": f"Total sent messages: {total_sent_messages}"}
    requests.post(url, json=data_json)
