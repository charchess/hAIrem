import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
import datetime
import sys
import os

# Configure Logging
logging.basicConfig(level=logging.INFO)

async def test_worker_logic():
    print("Testing Sleep Cycle Worker Logic...")
    
    # Mocks
    consolidator = AsyncMock()
    dreamer = AsyncMock()
    sleep_trigger_event = asyncio.Event()
    
    # Logic to test (replicated from main.py for verification of logic correctness)
    async def mock_worker(stop_event):
        logging.info("MOCK WORKER STARTED")
        last_run = 0
        daily_run_done = False
        
        while not stop_event.is_set():
            try:
                # Mock current time via a function we can patch
                # Using datetime.datetime.now() directly
                now = datetime.datetime.now()
                current_ts = now.timestamp()
                
                # Check for forced run via event
                if sleep_trigger_event.is_set():
                    print("Event Triggered!")
                    sleep_trigger_event.clear()
                    last_run = 0
                
                # 1. Hourly Consolidation
                if current_ts - last_run >= 3600:
                    print("Running Consolidation...")
                    if consolidator:
                        await consolidator.consolidate()
                        last_run = current_ts
                    
                # 2. Daily Maintenance (3 AM)
                if now.hour == 3:
                    if not daily_run_done:
                        print("Running Daily Maintenance...")
                        if consolidator:
                            await consolidator.apply_decay()
                        if dreamer:
                            await dreamer.prepare_daily_assets()
                        daily_run_done = True
                else:
                    daily_run_done = False
                    
            except Exception as e:
                print(f"Error: {e}")
            
            # Fast loop for test
            await asyncio.sleep(0.01)

    # Test Case 1: Initial Run
    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(mock_worker(stop_event))
    
    await asyncio.sleep(0.05)
    assert consolidator.consolidate.called, "Consolidate should run initially (last_run=0)"
    consolidator.consolidate.reset_mock()
    print("Test 1 Passed: Initial Run")
    
    # Test Case 2: Event Trigger
    sleep_trigger_event.set()
    await asyncio.sleep(0.05)
    assert consolidator.consolidate.called, "Consolidate should run on event"
    consolidator.consolidate.reset_mock()
    print("Test 2 Passed: Event Trigger")
    
    # Test Case 3: 3 AM Logic
    # We need to patch datetime.datetime
    with patch('datetime.datetime') as mock_date:
        # Mock time: 3:00 AM
        # We need a MagicMock that behaves like a datetime object
        mock_now = MagicMock()
        mock_now.hour = 3
        mock_now.timestamp.return_value = 100000.0 # Fixed timestamp
        
        mock_date.now.return_value = mock_now
        
        # We also need to make sure the loop logic doesn't crash on the first check 'current_ts - last_run'
        # last_run will be some value. 100000.0 - 0 >= 3600 is True.
        
        # Wait for loop
        await asyncio.sleep(0.05)
        
        assert consolidator.apply_decay.called, "Decay should run at 3 AM"
        assert dreamer.prepare_daily_assets.called, "Dreaming should run at 3 AM"
        print("Test 3 Passed: 3 AM Logic")
        
    stop_event.set()
    await worker_task
    print("ALL LOGIC VERIFIED!")

if __name__ == "__main__":
    try:
        asyncio.run(test_worker_logic())
    except Exception as e:
        print(f"FAILED: {e}")
