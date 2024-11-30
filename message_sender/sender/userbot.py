import logging
import asyncio
from telethon import TelegramClient
from typing import Dict, Any
import pandas as pd
from .utils import AccountManager, TelegramConfig, NotificationService, MESSAGES_PER_ACCOUNT, DELAY_BETWEEN_MESSAGES

# Configure logging
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure notification service
NOTIFICATION_SERVICE = NotificationService(
    bot_token="7767200091:AAETCGDplMsJHad-6vzhzPp-yt2YdavCsCE",
    chat_id="-1002213203187"
)

class MessageSender:
    def __init__(self, client: TelegramClient):
        self.client = client

    async def send_message(self, name: str, username: str, message: str) -> bool:
        """Send a message to a user with error handling."""
        try:
            formatted_message = message.replace('$name', name)
            await self.client.send_message(username, formatted_message)
            logger.info(f"Message sent to {name} ({username})")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {name} ({username}): {e}")
            return False

class TelegramSession:
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.client = TelegramClient(
            self.config.session_file,
            self.config.api_id,
            self.config.api_hash
        )

    async def __aenter__(self):
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

async def process_account(
    account_id: str,
    account_data: Dict[str, Any],
    data: pd.DataFrame,
    message: str,
    stop_flag: bool = None
) -> int:
    """Process a single account's messages."""
    from sender.views import stop_thread  # Import here to avoid circular import
    
    if not account_data['status'] or stop_thread:
        logger.info(f"Account {account_id} is inactive or stop requested before start")
        return 0

    config = TelegramConfig(account_data['api_id'], account_data['api_hash'])
    messages_sent = 0

    try:
        async with TelegramSession(config) as client:
            sender = MessageSender(client)
            logger.info(f"Processing messages for {account_id}")

            for index, row in data.iterrows():
                # Check stop flag before each message
                if stop_thread:
                    logger.info(f"Stop requested for {account_id} after {messages_sent} messages")
                    break

                if messages_sent >= MESSAGES_PER_ACCOUNT:
                    logger.info(f"Reached message limit for {account_id}")
                    break

                try:
                    # Check stop flag before sending
                    if stop_thread:
                        break
                        
                    if await sender.send_message(row['Name'], row['Username'], message):
                        messages_sent += 1
                        # Check stop flag before delay
                        if stop_thread:
                            break
                        await asyncio.sleep(DELAY_BETWEEN_MESSAGES)
                except Exception as e:
                    logger.error(f"Error sending message from {account_id}: {e}")
                    continue

            # Final notification
            if messages_sent > 0:
                await NOTIFICATION_SERVICE.send_notification(
                    f"{account_id} sent: {messages_sent} messages"
                )
    except Exception as e:
        logger.error(f"Error in process_account for {account_id}: {e}")
    finally:
        if stop_thread:
            logger.info(f"Account {account_id} stopped. Messages sent: {messages_sent}")

    return messages_sent

async def receive_data(data: pd.DataFrame, message: str) -> None:
    """Main function to process all accounts and send messages."""
    from sender.views import stop_thread  # Import here to avoid circular import

    account_manager = AccountManager()
    accounts = account_manager.read_accounts()
    total_sent_messages = 0
    active_accounts = 0

    for account_id, account_data in accounts.items():
        if stop_thread:
            logger.info("Message sending stopped by user")
            break

        messages_sent = await process_account(
            account_id, account_data, data, message
        )
        
        if messages_sent > 0:
            active_accounts += 1
            total_sent_messages += messages_sent
            account_manager.update_account_status(account_id, False)

        if data.empty:
            break

    if active_accounts == 0:
        logger.warning("No active accounts found")

    await NOTIFICATION_SERVICE.send_notification(
        f"Total sent messages: {total_sent_messages}"
    )
