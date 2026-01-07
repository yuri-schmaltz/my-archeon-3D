# my-hunyuan-3D API Documentation

## Overview
The `my-hunyuan-3D` API provides a RESTful interface for generating 3D assets (meshes and textures) from images or text prompts using the Tencent Hunyuan3D architecture.

It features a **Unified Inference Pipeline** managed by a **Priority Request Manager** with Lazy Loading support, ensuring efficient VRAM usage.

## Base URL
`http://localhost:8081` (Default)

## Endpoints

### 1. Generate 3D Model
**POST** `/generate`

Queues a generation task.

**Request Body (JSON):**
| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `image` | string | Base64 encoded input image (optional if text provided) | null |
| `text` | string | Text prompt for Text-to-Image generation (optional) | null |
| `seed` | int | Random seed for reproducibility | 1234 |
| `octree_resolution` | int | Resolution of the octree for shape generation | 128 |
| `num_inference_steps` | int | Number of diffusion steps | 5 |
| `guidance_scale` | float | Classifier-free guidance scale | 5.0 |
| `texture` | bool | If `true`, generates texture for the mesh | false |
| `face_count` | int | Target face count if texture is enabled | 40000 |
| `type` | string | Output format: `glb` or `obj` | `glb` |

**Response:**
Returns the binary file (GLB/OBJ) directly upon completion. 
*Note: Due to the blocking nature of the current implementation, this request stays open until generation finishes.*

---

### 2. Send Task (Async)
**POST** `/send`

Queues a generation task and returns immediately with a task ID (UID).

**Request Body:** Same as `/generate`.

**Response (JSON):**
```json
{
  "uid": "uuid-string"
}
```

---

### 3. Check Task Status
**GET** `/status/{uid}`

Checks the status of a task submitted via `/send`.

**Response (JSON):**
- **Processing:** `{"status": "processing"}`
- **Completed:** `{"status": "completed", "model_base64": "..."}`

---

### 4. Metrics (Observability)
**GET** `/metrics`

Returns Prometheus-formatted metrics for monitoring.

**Key Metrics:**
- `app_request_count`: Total HTTP requests counter (labeled by method, endpoint, status).
- `app_request_latency_seconds`: Histogram of request processing time.
- `app_generation_total`: Counter for generation jobs (started, success, error).

## Architecture Notes
- **Lazy Loading:** Models are not loaded into VRAM until the first request is made.
- **LRU Eviction:** If multiple models are registered (e.g., T2I vs I23D), the manager attempts to keep the utilized one in VRAM and offload others if capacity is reached.
