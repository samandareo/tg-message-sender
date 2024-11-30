from message_sender.scheduler import start_scheduler

default_app_config = 'message_sender.apps.MessageSenderConfig'

# Initialize the scheduler
scheduler = start_scheduler()