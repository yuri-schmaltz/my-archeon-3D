import trimesh
import numpy as np
import asyncio
import os
import unittest
from hy3dgen.meshops import tex_ops
from hy3dgen.api.schemas import MapType

class TestNativeTexturing(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        # Create a simple high-poly (sphere) and low-poly (cube)
        self.high_poly = trimesh.creation.uv_sphere(radius=1.0, count=[32, 32])
        self.low_poly = trimesh.creation.box(extents=[2, 2, 2])
        
    def test_generate_uvs(self):
        # Cube initially has no UVs in trimesh default creation (sometimes)
        # or has them but we want to re-generate.
        mesh = tex_ops.generate_uvs(self.low_poly)
        self.assertTrue(hasattr(mesh.visual, 'uv'))
        self.assertIsNotNone(mesh.visual.uv)
        self.assertEqual(len(mesh.visual.uv), len(mesh.vertices))
        print(f"UV generation verified: {len(mesh.faces)} faces, {len(mesh.visual.uv)} UV coords")

    async def test_bake_maps_native(self):
        maps = ["normal", "ao"]
        # Use low resolution for speed in test
        results = await tex_ops.bake_maps_native(self.high_poly, self.low_poly, maps, resolution=256)
        
        self.assertIn("normal", results)
        self.assertIn("ao", results)
        
        for mtype, path in results.items():
            self.assertTrue(os.path.exists(path))
            from PIL import Image
            img = Image.open(path)
            self.assertEqual(img.size, (256, 256))
            print(f"Native baking verified for {mtype}: {path}")

if __name__ == "__main__":
    unittest.main()
