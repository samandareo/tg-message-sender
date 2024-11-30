from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import json
from datetime import datetime
import os
import pytz

def notify_about_active(acc):
    BOT_TOKEN = 'BOT_TOKEN'
    CHAT_ID = 'CHAT_ID'
    NOTIFICATION_SERVICE = NotificationService(
    bot_token="7767200091:AAETCGDplMsJHad-6vzhzPp-yt2YdavCsCE",
    chat_id="-1002213203187")
    message = f"Account {acc} is active"
    NOTIFICATION_SERVICE.send_notification(message)

def update_account_status():
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'sessions', 'accounts.json')
        
        # Read the current accounts data
        with open(json_path, 'r') as f:
            accounts = json.load(f)
        
        current_time = datetime.now(pytz.UTC)
        modified = False
        
        # Check each account
        for acc_id, acc_data in accounts.items():
            account_time = datetime.fromisoformat(acc_data['time'].replace('Z', '+00:00'))
            time_diff = current_time - account_time
            
            # If time difference is 24 hours or more and status is False
            if time_diff.total_seconds() >= 24 * 3600 and not acc_data['status']:
                acc_data['status'] = True
                modified = True
        
        # Save changes if any modifications were made
        if modified:
            notify_about_active(acc_id)
            with open(json_path, 'w') as f:
                json.dump(accounts, f, indent=4)
    
    except Exception as e:
        print(f"Error updating account status: {str(e)}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=update_account_status,
        trigger=IntervalTrigger(hours=2),
        id='update_account_status',
        name='Update account status every 2 hours',
        replace_existing=True
    )
    scheduler.start()
    return scheduler
