import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AccountManager:
    def __init__(self, accounts_file: str = 'sessions/accounts.json'):
        self.accounts_file = accounts_file

    def read_accounts(self) -> Dict[str, Any]:
        """Read accounts from JSON file."""
        try:
            with open(self.accounts_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"Accounts file not found: {self.accounts_file}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in accounts file: {self.accounts_file}")
            return {}

    def write_accounts(self, accounts: Dict[str, Any]) -> None:
        """Write accounts to JSON file."""
        try:
            with open(self.accounts_file, 'w') as file:
                json.dump(accounts, file, indent=4)
        except Exception as e:
            logger.error(f"Failed to write accounts: {e}")

    def update_account_status(self, account_id: str, status: bool) -> None:
        """Update status of a single account."""
        accounts = self.read_accounts()
        if account_id in accounts:
            accounts[account_id].update({
                'status': status,
                'time': datetime.now().isoformat()
            })
            self.write_accounts(accounts)

    def get_active_accounts_count(self) -> int:
        """Get number of active accounts."""
        accounts = self.read_accounts()
        return sum(1 for acc in accounts.values() if acc['status'])

class TelegramConfig:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        
    @property
    def session_file(self) -> str:
        return f'sessions/acc_{self.api_id}'

class NotificationService:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async def send_notification(self, message: str) -> None:
        """Send notification via Telegram bot."""
        try:
            import requests
            data = {"chat_id": self.chat_id, "text": message}
            response = requests.post(self.base_url, json=data)
            if response.status_code != 200:
                logger.error(f"Failed to send notification: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

# Constants
MESSAGES_PER_ACCOUNT = 100
DELAY_BETWEEN_MESSAGES = 1/0.05  # 20 seconds
