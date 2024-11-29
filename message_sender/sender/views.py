import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import asyncio
import threading
from .userbot import receive_data
from .utils import AccountManager

# Thread management
background_thread = None
stop_thread = False

class AsyncMessageProcessor:
    def __init__(self, data: pd.DataFrame, message: str):
        self.data = data
        self.message = message

    def run_async(self):
        """Run async code in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(receive_data(self.data, self.message))
        finally:
            loop.close()

class ThreadManager:
    @staticmethod
    def start_new_thread(processor: AsyncMessageProcessor) -> threading.Thread:
        """Start a new thread for message processing."""
        thread = threading.Thread(target=processor.run_async)
        thread.start()
        return thread

    @staticmethod
    def stop_current_thread() -> bool:
        """Stop the currently running thread."""
        global background_thread, stop_thread
        if background_thread and background_thread.is_alive():
            stop_thread = True
            background_thread.join()
            background_thread = None
            return True
        return False

@require_http_methods(["GET"])
def index(request):
    """Render the index page."""
    return render(request, 'sender/index.html')

@require_http_methods(["GET"])
def check_status(request):
    """Check the current status of message sending."""
    account_manager = AccountManager()
    is_running = bool(background_thread and background_thread.is_alive())
    
    return JsonResponse({
        'active_accounts': account_manager.get_active_accounts_count(),
        'is_running': is_running
    })

@require_http_methods(["GET"])
def stop_sender(request):
    """Stop the message sending process."""
    was_stopped = ThreadManager.stop_current_thread()
    
    return JsonResponse({
        'message': 'Message sending stopped successfully' if was_stopped 
                  else 'No active sending process to stop'
    })

@require_http_methods(["GET", "POST"])
def message_sender(request):
    """Handle message sending requests."""
    global background_thread, stop_thread
    
    if request.method == 'GET':
        return render(request, 'sender/message_sender.html')

    # POST request handling
    message = request.POST.get('message', '')
    file = request.FILES.get('file')

    if not file or not message:
        return JsonResponse({
            'error': 'Both message and file are required'
        }, status=400)

    try:
        # Stop any existing thread
        ThreadManager.stop_current_thread()
        
        # Reset the stop flag
        stop_thread = False
        
        # Process the Excel file
        data = pd.read_excel(file)
        
        # Start new background thread
        processor = AsyncMessageProcessor(data, message)
        background_thread = ThreadManager.start_new_thread(processor)

        return JsonResponse({
            'message': 'Message sending started in background. You can stop it anytime.',
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Failed to process file: {str(e)}'
        }, status=500)