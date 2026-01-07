import unittest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock torch before imports
sys.modules['torch'] = MagicMock()
sys.modules['hy3dgen.shapegen.utils'] = MagicMock()


from hy3dgen.manager import ModelManager, PriorityRequestManager

class TestModelManager(unittest.TestCase):
    def setUp(self):
        self.manager = ModelManager(capacity=1, device='cpu')

    def test_register_and_load(self):
        """Test that we can register a loader and it is only called when accessed."""
        mock_loader = MagicMock(return_value="ModelInstance")
        
        self.manager.register_model("test_model", mock_loader)
        
        # Shouldn't be loaded yet
        self.assertEqual(len(self.manager.workers), 0)
        mock_loader.assert_not_called()
        
        # Access it
        worker = asyncio.run(self.manager.get_worker("test_model"))
        
        self.assertEqual(worker, "ModelInstance")
        self.assertEqual(len(self.manager.workers), 1)
        mock_loader.assert_called_once()
        
        # Access again - shouldn't load again
        asyncio.run(self.manager.get_worker("test_model"))
        mock_loader.assert_called_once()

    def test_lru_eviction(self):
        """Test that the capacity limit enforces LRU eviction."""
        self.manager.capacity = 1
        
        loader_a = MagicMock(return_value="ModelA")
        loader_b = MagicMock(return_value="ModelB")
        
        self.manager.register_model("A", loader_a)
        self.manager.register_model("B", loader_b)
        
        # Load A
        asyncio.run(self.manager.get_worker("A"))
        self.assertIn("A", self.manager.workers)
        
        # Load B - should evict A
        asyncio.run(self.manager.get_worker("B"))
        self.assertIn("B", self.manager.workers)
        self.assertNotIn("A", self.manager.workers)
        self.assertEqual(len(self.manager.workers), 1)

    def test_priority_request(self):
        """Test submitting a job through PriorityRequestManager."""
        
        # Mock a worker
        mock_worker = MagicMock()
        mock_worker.generate = MagicMock(return_value="Result")
        
        # Manager with loader
        model_mgr = ModelManager(capacity=1)
        model_mgr.register_model("primary", lambda: mock_worker)
        
        req_mgr = PriorityRequestManager(model_mgr, max_concurrency=1)
        
        async def run_test():
            await req_mgr.start()
            
            # Submit job
            params = {"model_key": "primary", "data": "foo"}
            result = await req_mgr.submit(params)
            
            self.assertEqual(result, "Result")
            mock_worker.generate.assert_called()
            
            await req_mgr.stop()

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
