import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from sender.userbot import receive_data
import asyncio
import threading
import json

# Global variable to store the background thread
background_thread = None
stop_thread = False

def index(request):
    return render(request, 'sender/index.html')

def run_async_receive_data(data, message):
    global stop_thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(receive_data(data, message))
    finally:
        loop.close()

def stop_sender(request):
    global background_thread, stop_thread
    if background_thread and background_thread.is_alive():
        stop_thread = True
        background_thread.join()
        background_thread = None
        return JsonResponse({'message': 'Message sending stopped successfully'})
    return JsonResponse({'message': 'No active sending process to stop'})

def check_status(request):
    with open('sessions/accounts.json', 'r') as file:
        accounts = json.load(file)
    
    active_accounts = sum(1 for acc in accounts.values() if acc['status'])
    is_running = background_thread and background_thread.is_alive()
    
    return JsonResponse({
        'active_accounts': active_accounts,
        'is_running': is_running
    })

def message_sender(request):
    global background_thread, stop_thread
    
    if request.method == 'GET':
        return render(request, 'sender/message_sender.html')

    elif request.method == 'POST':
        message = request.POST.get('message', '')
        file = request.FILES.get('file')

        if not file or not message:
            return JsonResponse({'error': 'Both message and file are required'}, status=400)

        try:
            # Stop any existing thread
            if background_thread and background_thread.is_alive():
                stop_thread = True
                background_thread.join()

            # Reset the stop flag
            stop_thread = False
            
            # Process the Excel file
            data = pd.read_excel(file)
            
            # Start new background thread
            background_thread = threading.Thread(
                target=run_async_receive_data,
                args=(data, message)
            )
            background_thread.start()

            return JsonResponse({
                'message': 'Message sending started in background. You can stop it anytime.',
            })

        except Exception as e:
            return JsonResponse({'error': f'Failed to process file: {str(e)}'}, status=500)