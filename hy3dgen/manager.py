import asyncio
import uuid
import time
import torch
import threading
import gc
from dataclasses import dataclass, field
from typing import Any, Dict, Callable
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
    Supports lazy loading of models.
    """
    def __init__(self, capacity: int = 1, device: str = 'cuda'):
        self.workers = {}  # key -> model_instance
        self.loaders = {}  # key -> loader_function
        self.capacity = capacity
        self.device = device
        self.lock = asyncio.Lock()
        self.lru_order = []  # List of keys, most recently used at the end

    def register_model(self, key: str, loader: Callable[[], Any]):
        """Register a model loader without loading it immediately."""
        self.loaders[key] = loader
        logger.info(f"Registered model loader for: {key}")

    async def get_worker(self, model_key: str):
        """
        Retrieves a worker for the given key. Loads it if necessary, evicting others.
        """
        if model_key in self.workers:
            # Move to end (most recently used)
            if model_key in self.lru_order:
                self.lru_order.remove(model_key)
            self.lru_order.append(model_key)
            return self.workers[model_key]
        
        # Check if we have a loader
        if model_key not in self.loaders:
            raise ValueError(f"No loader registered for model: {model_key}")

        logger.info(f"Loading model '{model_key}'...")
        
        # Check capacity/eviction
        if len(self.workers) >= self.capacity:
            await self.offload_lru_model()

        # Load the model
        # Execute loader. Warning: This is synchronous blocking code if loader is not async.
        # Since standard torch loading is blocking, we might want to run in executor if necessary, 
        # but for simplicity here we assume it's acceptable or wrapped.
        start_time = time.time()
        try:
            self.workers[model_key] = self.loaders[model_key]()
            self.lru_order.append(model_key)
            logger.info(f"Model '{model_key}' loaded in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.warning(f"Initial load of model '{model_key}' failed: {e}. Attempting to clear VRAM and retry...")
            
            # Emergency Cleanup
            if self.device == 'cuda':
                gc.collect()
                torch.cuda.empty_cache()
            
            # Evict everything we can
            while self.workers:
                await self.offload_lru_model()
            
            # Retry load
            try:
                 self.workers[model_key] = self.loaders[model_key]()
                 self.lru_order.append(model_key)
                 logger.info(f"Model '{model_key}' loaded successfully on retry.")
            except Exception as e2:
                 logger.error(f"Failed to load model '{model_key}' even after cleanup: {e2}")
                 raise e2

        return self.workers[model_key]

    async def offload_lru_model(self):
        """Offload the least recently used model."""
        if not self.lru_order:
            return

        lru_key = self.lru_order.pop(0)
        logger.info(f"Offloading model: {lru_key}")
        
        if lru_key in self.workers:
            model = self.workers[lru_key]
            del self.workers[lru_key]
            # Explicit cleanup hint
            del model
            
            if self.device == 'cuda':
                gc.collect()
                torch.cuda.empty_cache()
                logger.info("VRAM cleared (gc + empty_cache).")

    async def generate_safe(self, uid, params, loop):
        """
        Executes generation ensuring thread safety and VRAM management.
        """
        async with self.lock:
            # Determine which model to use. Default to 'primary' if not configured.
            model_key = params.get("model_key", "primary")

            # Notify user about loading state
            progress_callback = params.get("progress_callback")
            if progress_callback:
                try:
                    progress_callback(0, f"Loading model '{model_key}' (this may take a while)...")
                except Exception:
                    pass
            
            # Retrieve (load) worker
            worker = await self.get_worker(model_key)
            
            # logger.info(f"Using worker for model: {model_key}")
            
            # Run generation in executor to avoid blocking the async loop
            result = await loop.run_in_executor(
                None, 
                worker.generate, 
                uid, 
                params
            )
            
            # Aggressive cleanup after generation
            if self.device == 'cuda':
                gc.collect()
                torch.cuda.empty_cache()
            
            return result

class PriorityRequestManager:
    def __init__(self, model_manager: ModelManager = None, max_concurrency: int = 1):
        if model_manager is None:
            # Default empty manager if none provided
            self.model_manager = ModelManager()
        else:
            self.model_manager = model_manager
            
        self.queue = asyncio.PriorityQueue()
        self.max_concurrency = max_concurrency
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

    async def submit(self, params: Dict[str, Any], priority: int = 10, uid: str = None) -> Any:
        """Submit a job to the queue and wait for result."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        if uid is None:
            uid = str(uuid.uuid4())
        
        item = PrioritizedItem(
            priority=priority,
            timestamp=time.time(),
            uid=uid,
            params=params,
            future=future
        )
        
        # Create cancel event for this job
        cancel_event = threading.Event()
        item.params['cancel_event'] = cancel_event
        
        await self.queue.put(item)
        logger.info(f"Job {uid} queued with priority {priority}. Queue size: {self.queue.qsize()}")
        
        # Wait for the result with cancellation support
        try:
            return await future
        except asyncio.CancelledError:
            logger.info(f"Job {uid} cancelled by caller.")
            cancel_event.set()
            # We also need to cancel the future if it wasn't already?
            # If we are here, caller cancelled the *await*, so we must ensure future is marked cancelled
            # so worker knows to stop or ignore result.
            if not future.done():
                future.cancel()
            raise

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
