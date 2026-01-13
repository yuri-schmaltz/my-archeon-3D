# API Reference - Hunyuan3D-2

Auto-generated API documentation from source code docstrings.

## Table of Contents

- [Core Managers](#core-managers)
- [Inference Pipeline](#inference-pipeline)
- [Shape Generation](#shape-generation)
- [Texture Generation](#texture-generation)
- [Mesh Operations](#mesh-operations)
- [Web Applications](#web-applications)

---

## Core Managers

### ModelManager

**Module:** `hy3dgen.manager.ModelManager`

Manages loaded models and inference resources.

**Key Methods:**

- `__init__(device='cuda', cache_dir=None)` - Initialize model manager
- `load_shape_models()` - Load shape generation models
- `load_texture_models()` - Load texture generation models
- `inference_shape(prompt, **kwargs)` - Generate 3D shape from text
- `inference_texture(shape, **kwargs)` - Generate texture on shape
- `cleanup()` - Release GPU memory

**Example:**
```python
from hy3dgen.manager import ModelManager

manager = ModelManager(device='cuda')
manager.load_shape_models()
manager.load_texture_models()

shape = manager.inference_shape("A red ceramic vase")
textured = manager.inference_texture(shape)
```

### PriorityRequestManager

**Module:** `hy3dgen.manager.PriorityRequestManager`

Manages request queues with priority scheduling.

**Key Methods:**

- `__init__(max_queue_size=100)` - Initialize queue manager
- `add_request(prompt, priority=0, callback=None)` - Add request to queue
- `process_queue()` - Process queued requests
- `get_request_status(request_id)` - Check request status
- `cancel_request(request_id)` - Cancel queued request

---

## Inference Pipeline

### InferencePipeline

**Module:** `hy3dgen.inference.InferencePipeline`

Complete pipeline for shape-to-texture generation.

**Key Methods:**

- `__init__(model_manager, use_rembg=True)` - Initialize pipeline
- `generate(prompt, negative_prompt='', steps=50, **kwargs)` - Full generation
- `process_image(image_path)` - Preprocess input image
- `remove_background(image)` - Remove image background
- `export_glb(mesh, texture, output_path)` - Export to GLB format

**Supported Formats:**

- Input: Prompts (text), Images (PNG, JPG)
- Output: GLB 3D models with PBR textures

---

## Shape Generation

### ShapeGenPipeline

**Module:** `hy3dgen.shapegen.pipelines`

Generates 3D shapes from text or images.

**Features:**

- Text-to-shape synthesis
- Image-to-shape reconstruction
- Multi-view consistency
- Mesh quality optimization

**Key Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | str | - | Text description of shape |
| `num_steps` | int | 50 | Diffusion steps |
| `guidance_scale` | float | 7.5 | Classifier-free guidance |
| `seed` | int | None | Random seed |

**Output:** 3D mesh (trimesh.Trimesh)

---

## Texture Generation

### TextureGenPipeline

**Module:** `hy3dgen.texgen.pipelines`

Generates PBR textures for 3D meshes.

**Features:**

- Automatic UV unwrapping
- PBR map generation (albedo, normal, roughness, metallic)
- Multi-view painting
- High-resolution texture export

**Key Methods:**

- `paint_mesh(mesh, prompt)` - Generate texture from prompt
- `refine_texture(mesh, num_iterations=5)` - Iterative refinement
- `export_maps(output_dir)` - Save PBR maps separately

---

## Mesh Operations

### MeshUtils

**Module:** `hy3dgen.shapegen.utils`

Utility functions for mesh processing.

**Key Functions:**

```python
# Create mesh from vertices/faces
mesh = create_mesh_from_arrays(vertices, faces)

# Copy mesh preserving properties (texture, color, etc)
mesh_copy = mesh_copy_preserve_all(mesh)

# Validate mesh integrity
is_valid = validate_mesh(mesh)

# Optimize mesh topology
optimized = simplify_mesh(mesh, target_count=50000)
```

### MeshRender

**Module:** `hy3dgen.shapegen.mesh_render`

Rendering and visualization operations.

**Key Methods:**

```python
# Render mesh to image
image = render_mesh_to_image(mesh, width=512, height=512)

# Export to GLB with embedded textures
export_mesh_glb(mesh, texture_path, output_path)

# Convert mesh format (OBJ, FBX, GLTF, etc)
convert_mesh_format(input_path, output_format)
```

---

## Web Applications

### Gradio Interface

**Module:** `hy3dgen.apps.gradio_app`

Interactive web UI for shape and texture generation.

**Features:**

- Text-to-3D with live preview
- Image upload for texture reference
- Real-time generation progress
- GLB download

**Usage:**

```bash
python -m hy3dgen.apps.gradio_app
# Runs on http://localhost:7860
```

### FastAPI REST API

**Module:** `hy3dgen.apps.api_server`

REST API for programmatic access.

**Endpoints:**

#### POST `/api/v1/generate/shape`
Generate 3D shape from prompt.

**Request:**
```json
{
  "prompt": "A wooden chair",
  "negative_prompt": "",
  "num_steps": 50,
  "guidance_scale": 7.5
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "status": "processing",
  "progress": 0.45
}
```

#### POST `/api/v1/generate/texture`
Add texture to existing mesh.

**Request:**
```json
{
  "mesh_id": "uuid",
  "prompt": "Red leather texture"
}
```

#### GET `/api/v1/download/{request_id}`
Download generated GLB model.

#### GET `/api/v1/status/{request_id}`
Check generation progress.

---

## Configuration

### Environment Variables

```bash
# Device selection
HY3D_DEVICE=cuda              # or 'cpu'

# Model caching
HY3D_MODEL_CACHE=/path/to/cache

# API server
HY3D_API_HOST=0.0.0.0
HY3D_API_PORT=8000

# Gradio interface
HY3D_GRADIO_SHARE=false
HY3D_GRADIO_QUEUE_ENABLED=true
```

### Python Configuration

```python
from hy3dgen.manager import ModelManager

config = {
    'device': 'cuda',
    'dtype': 'float16',
    'max_batch_size': 4,
    'enable_xformers': True,
}

manager = ModelManager(**config)
```

---

## Common Workflows

### Generate 3D Model from Prompt

```python
from hy3dgen.inference import InferencePipeline
from hy3dgen.manager import ModelManager

manager = ModelManager()
pipeline = InferencePipeline(manager)

# Generate
result = pipeline.generate(
    prompt="A ceramic teapot with blue glaze",
    steps=50
)

# Export
result.mesh.export('teapot.glb')
```

### Add Texture to Existing Mesh

```python
from hy3dgen.texgen.pipelines import TextureGenPipeline

texture_gen = TextureGenPipeline()
textured_mesh = texture_gen.paint_mesh(
    mesh=loaded_mesh,
    prompt="Weathered bronze texture"
)

texture_gen.export_maps('./textures/')
```

### Batch Processing

```python
from hy3dgen.manager import PriorityRequestManager

queue = PriorityRequestManager()

prompts = [
    ("A red cube", 1),
    ("A blue sphere", 0),
    ("A green pyramid", 2),
]

for prompt, priority in prompts:
    queue.add_request(prompt, priority=priority)

queue.process_queue()
```

---

## Performance Metrics

### Generation Times (on NVIDIA A100)

| Task | Time | Memory |
|------|------|--------|
| Shape generation (50 steps) | ~8 seconds | ~15GB |
| Texture generation | ~5 seconds | ~8GB |
| Full pipeline | ~13 seconds | ~20GB |

### Model Sizes

| Model | Size | Device |
|-------|------|--------|
| Shape model (DiT) | 5.2GB | GPU |
| Texture model | 3.8GB | GPU |
| Conditioning models | 2.1GB | GPU |

---

## Troubleshooting

### Out of Memory Errors

```python
# Reduce batch size and enable optimization
manager = ModelManager(
    device='cuda',
    enable_memory_efficient=True,
    max_batch_size=1
)
```

### Slow Generation

```python
# Enable TorchScript compilation and xFormers
manager = ModelManager(
    enable_xformers=True,
    use_torch_compile=True,
)
```

### Missing Textures in Export

```python
# Ensure texture is properly attached
from hy3dgen.shapegen.mesh_utils import ensure_texture_on_mesh

mesh = ensure_texture_on_mesh(mesh)
mesh.export('model.glb')
```

---

## API Version

**Current Version:** 2.2.0  
**Last Updated:** 2024  
**Documentation Generated:** Auto from docstrings

For detailed source code documentation, see the inline docstrings in each module.

