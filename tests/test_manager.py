import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from hy3dgen.manager import PriorityRequestManager, ModelManager

@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_manager_flow():
    # 1. Setup Mock ModelManager
    mock_model_mgr = MagicMock(spec=ModelManager)
    # generate_safe must be an async method (or return a future/coroutine)
    # In manager.py, generate_safe is async.
    mock_model_mgr.generate_safe = AsyncMock(return_value={"status": "ok", "uid": "test-uid", "mesh": "mock_mesh", "stats": {}})

    # 2. Initialize Manager
    manager = PriorityRequestManager(model_manager=mock_model_mgr, max_concurrency=1)
    
    # Start the manager loop
    await manager.start()
    
    try:
        # 3. Submit a job
        params = {"text": "test prompt", "model_key": "Normal"}
        # Priority 10 is default
        future = asyncio.create_task(manager.submit(params, priority=10))
        
        # 4. Wait for result
        result = await future
        
        # 5. Assertions
        assert result["status"] == "ok"
        assert result["uid"] == "test-uid"
        
        # Verify generate_safe was called with expected args
        # It's called with (uid, params, loop)
        mock_model_mgr.generate_safe.assert_called_once()
        args, _ = mock_model_mgr.generate_safe.call_args
        assert args[1] == params  # Verify params passed correctly

    finally:
        # Cleanup
        await manager.stop()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_request_manager_priority():
    """Test that higher priority items (lower number) are processed first if queued together."""
    mock_model_mgr = MagicMock(spec=ModelManager)
    # Add a small delay to simulate processing allowing queue to fill
    async def side_effect(uid, params, loop):
        await asyncio.sleep(0.1) 
        return uid
    
    mock_model_mgr.generate_safe = AsyncMock(side_effect=side_effect)

    manager = PriorityRequestManager(model_manager=mock_model_mgr, max_concurrency=1)
    await manager.start()
    
    try:
        # Submit 3 jobs. The first one starts immediately.
        # Job 1 (Priority 10) - Starts immediately
        task1 = asyncio.create_task(manager.submit({"id": 1}, priority=10))
        
        # Give a split second for worker to pick up task1
        await asyncio.sleep(0.01)
        
        # Now submit Job 2 (Priority 20) and Job 3 (Priority 1)
        # Worker is busy with task1. Queue should order task3 before task2.
        task2 = asyncio.create_task(manager.submit({"id": 2}, priority=20))
        task3 = asyncio.create_task(manager.submit({"id": 3}, priority=1))
        
        results = await asyncio.gather(task1, task2, task3)
        
        # We can inspect the order of calls in the mock
        # calls should be: task1 -> task3 -> task2
        # (Assuming worker picked up task1, then checked queue which had [task3, task2])
        
        assert mock_model_mgr.generate_safe.call_count == 3
        calls = mock_model_mgr.generate_safe.call_args_list
        
        # Extract params from calls
        executed_params = [c.args[1] for c in calls]
        
        # 1st execution: {"id": 1}
        assert executed_params[0]["id"] == 1
        
        # 2nd execution shoud be {"id": 3} (Priority 1) 
        # Note: PriorityQueue uses lowest number as highest priority.
        assert executed_params[1]["id"] == 3
        
        # 3rd execution: {"id": 2} (Priority 20)
        assert executed_params[2]["id"] == 2
        
    finally:
        await manager.stop()
