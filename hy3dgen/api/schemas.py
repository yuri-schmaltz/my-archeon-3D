from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, constr, conint, confloat
from uuid import uuid4
from enum import Enum

# --- Enums ---

class Mode(str, Enum):
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    TEXT_IMAGE_TO_3D = "text_image_to_3d"
    REFINE_3D = "refine_3d"

class Role(str, Enum):
    REFERENCE = "reference"
    ORTHOGRAPHIC_FRONT = "orthographic_front"
    ORTHOGRAPHIC_BACK = "orthographic_back"
    ORTHOGRAPHIC_LEFT = "orthographic_left"
    ORTHOGRAPHIC_RIGHT = "orthographic_right"
    ORTHOGRAPHIC_TOP = "orthographic_top"
    ORTHOGRAPHIC_BOTTOM = "orthographic_bottom"

class MeshFormat(str, Enum):
    GLB = "glb"
    OBJ = "obj"
    FBX = "fbx"
    STL = "stl"

class ScaleUnit(str, Enum):
    M = "m"
    CM = "cm"
    MM = "mm"

class Pivot(str, Enum):
    CENTER = "center"
    BOTTOM_CENTER = "bottom_center"

class Axis(str, Enum):
    Y_UP = "y_up"
    Z_UP = "z_up"

class MapType(str, Enum):
    BASECOLOR = "basecolor"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    AO = "ao"
    EMISSIVE = "emissive"

class BackgroundMode(str, Enum):
    REMOVE = "remove"
    KEEP = "keep"

class Symmetry(str, Enum):
    NONE = "none"
    X = "x"
    Y = "y"
    Z = "z"

class RiggingType(str, Enum):
    HUMANOID = "humanoid"
    GENERIC = "generic"

class QualityPreset(str, Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"

class Determinism(str, Enum):
    BEST_EFFORT = "best_effort"
    STRICT = "strict"

class JobStatus(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    PREPROCESSING = "preprocessing"
    GENERATING = "generating"
    POSTPROCESSING = "postprocessing"
    QA = "qa"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    COMPLETED_PARTIAL = "completed_partial"

class ArtifactType(str, Enum):
    MESH = "mesh"
    TEXTURES = "textures"
    PREVIEW_RENDERS = "preview_renders"
    REPORT = "report"

# --- Models ---

class ImageItem(BaseModel):
    image_id: str = Field(..., min_length=1, max_length=64)
    uri: str = Field(..., min_length=3)
    role: Role
    mask_uri: Optional[str] = Field(None, min_length=3)

class SourceMesh(BaseModel):
    uri: str = Field(..., min_length=3)
    format: Optional[MeshFormat] = None

class Input(BaseModel):
    text_prompt: Optional[str] = Field(default="")
    negative_prompt: Optional[str] = None
    images: List[ImageItem] = Field(default_factory=list)
    source_mesh: Optional[SourceMesh] = None

class RealWorldSize(BaseModel):
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    z: float = Field(..., ge=0)
    unit: ScaleUnit

class PolyBudget(BaseModel):
    max_tris: int = Field(..., ge=500, le=5000000)
    prefer_quads: bool

class Topology(BaseModel):
    watertight: bool
    manifold: bool
    no_self_intersections: bool

class UV(BaseModel):
    required: bool
    max_islands: int = Field(0, ge=0, le=100000)

class Materials(BaseModel):
    pbr: bool
    texture_resolution: int # Enum validation via standard validation not explicit enum due to int
    maps: List[MapType]
    single_material: bool

class LOD(BaseModel):
    generate: bool
    levels: List[float] = Field(default_factory=list)

class Rigging(BaseModel):
    generate: bool
    type: RiggingType

class Constraints(BaseModel):
    target_format: List[MeshFormat]
    scale_unit: Optional[ScaleUnit] = None
    real_world_size: Optional[RealWorldSize] = None
    pivot: Optional[Pivot] = None
    axis: Optional[Axis] = None
    poly_budget: Optional[PolyBudget] = None
    topology: Optional[Topology] = None
    uv: Optional[UV] = None
    materials: Optional[Materials] = None
    background: Optional[BackgroundMode] = None
    symmetry: Optional[Symmetry] = None
    lod: Optional[LOD] = None
    rigging: Optional[Rigging] = None

class Quality(BaseModel):
    preset: QualityPreset
    steps: int = Field(0, ge=0, le=10000)
    seed: int = Field(0, ge=0)
    determinism: Determinism
    text_adherence: float = Field(0.0, ge=0.0, le=1.0)
    image_adherence: float = Field(0.0, ge=0.0, le=1.0)

class Postprocess(BaseModel):
    cleanup: bool
    retopo: bool
    decimate: bool
    bake_textures: bool
    mesh_simplify_target_tris: int = Field(0, ge=0, le=5000000)
    remove_hidden: bool
    fix_normals: bool
    generate_collision: bool

class Output(BaseModel):
    artifact_prefix: str = Field(..., min_length=1, max_length=128)
    return_preview_renders: bool
    preview_angles_deg: List[int] = Field(default=[0, 45, 90, 135, 180, 225, 270, 315])

# --- Top Level ---

class Batch(BaseModel):
    enabled: bool
    items: List[Dict[str, Any]] = Field(default_factory=list) # Recursive references are tricky, using Dict for payload
    concurrency_hint: int = Field(1, ge=1, max=256)

class JobRequest(BaseModel):
    request_id: str = Field(..., min_length=8, max_length=128)
    schema_version: str = Field("1.0", pattern=r"^1\.0$")
    mode: Mode
    input: Input
    constraints: Constraints
    quality: Quality
    postprocess: Postprocess
    batch: Batch
    output: Output

# --- Responses ---

class Bounds(BaseModel):
    x: float
    y: float
    z: float

class MeshMetadata(BaseModel):
    tris: int
    verts: int
    uv_sets: int
    materials_count: int
    watertight: bool
    manifold: bool
    axis: Axis
    unit: ScaleUnit
    pivot: Pivot
    bounds: Bounds

class Artifact(BaseModel):
    type: ArtifactType
    format: str
    uri: str
    metadata: Dict[str, Any]

class ErrorDetail(BaseModel):
    field: str
    issue: str
    suggestion: str

class ErrorObject(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail]
    retryable: bool

class JobResponse(BaseModel):
    request_id: str
    schema_version: str = "1.0"
    status: JobStatus
    artifacts: List[Artifact] = Field(default_factory=list)
    quality_report: Optional[Dict[str, Any]] = None # Simplified for now
    error: Optional[ErrorObject] = None

