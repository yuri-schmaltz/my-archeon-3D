import asyncio
import logging
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from hy3dgen.shapegen.utils import get_logger

logger = get_logger("manager")

@dataclass(order=True)
class PrioritizedItem:
    priority: int
    timestamp: float
    uid: str = field(compare=False)
    params: Dict[str, Any] = field(compare=False)
    future: asyncio.Future = field(compare=False)

class ModelManager:
    """
    Wraps ModelWorkers to provide thread safety, VRAM management, and LRU caching.
    """
    def __init__(self, primary_worker, capacity: int = 1):
        # In this simplified version, we primarily wrap a single worker
        # but structured to allow switching if we had multiple model paths.
        self.workers = {}
        self.primary_worker = primary_worker
        self.capacity = capacity
        self.lock = asyncio.Lock()
        
        # Initialize with the primary worker
        self.workers["primary"] = primary_worker
        self.lru_order = ["primary"]

    async def get_worker(self, model_key: str):
        """
        Retrieves a worker for the given key. Evicts old ones if needed.
        (Currently supports 'primary' only, but extensible).
        """
        if model_key in self.workers:
            # Move to end (most recently used)
            if model_key in self.lru_order:
                self.lru_order.remove(model_key)
            self.lru_order.append(model_key)
            return self.workers[model_key]
        
        # Logic to load new model would go here...
        # For now, default to primary
        logger.warning(f"Model key '{model_key}' not found, falling back to primary.")
        return self.primary_worker

    async def generate_safe(self, uid, params, loop):
        """
        Executes generation ensuring thread safety and VRAM management.
        """
        async with self.lock:
            # Determine which model to use (could be passed in params)
            model_key = params.get("model_key", "primary")
            worker = await self.get_worker(model_key)
            
            logger.info(f"Using worker for model: {model_key}")
            
            result = await loop.run_in_executor(
                None, 
                worker.generate, 
                uid, 
                params
            )
            
            # Explicit garbage collection if VRAM is tight
            # import torch; torch.cuda.empty_cache()  <-- already done in worker
            return result

class PriorityRequestManager:
    def __init__(self, worker_instance, max_concurrency: int = 1):
        self.model_manager = ModelManager(worker_instance)
        self.queue = asyncio.PriorityQueue()
        self.max_concurrency = max_concurrency
        self.active_workers = 0
        self.running = False
        self.workers = []

    async def start(self):
        """Start the background worker loops."""
        self.running = True
        logger.info(f"Starting PriorityRequestManager with {self.max_concurrency} workers.")
        for i in range(self.max_concurrency):
            task = asyncio.create_task(self._worker_loop(i))
            self.workers.append(task)

    async def stop(self):
        """Stop processing."""
        self.running = False
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)

    async def submit(self, params: Dict[str, Any], priority: int = 10) -> Any:
        """Submit a job to the queue and wait for result."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        uid = str(uuid.uuid4())
        
        item = PrioritizedItem(
            priority=priority,
            timestamp=time.time(),
            uid=uid,
            params=params,
            future=future
        )
        
        await self.queue.put(item)
        logger.info(f"Job {uid} queued with priority {priority}. Queue size: {self.queue.qsize()}")
        
        # Wait for the result
        return await future

    async def _worker_loop(self, worker_id: int):
        logger.info(f"Worker {worker_id} started.")
        while self.running:
            try:
                # Get a "work item" out of the queue.
                item: PrioritizedItem = await self.queue.get()
                
                logger.info(f"Worker {worker_id} processing job {item.uid} (priority {item.priority})")
                
                try:
                    loop = asyncio.get_running_loop()
                    # Use ModelManager for safe execution
                    result = await self.model_manager.generate_safe(item.uid, item.params, loop)
                    
                    if not item.future.cancelled():
                        item.future.set_result(result)
                        
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed job {item.uid}: {e}", exc_info=True)
                    if not item.future.cancelled():
                        item.future.set_exception(e)
                finally:
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} loop error: {e}", exc_info=True)
                await asyncio.sleep(1)  # Prevent tight loop on crash
