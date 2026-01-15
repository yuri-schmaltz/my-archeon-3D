from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, constr, conint, confloat, AliasChoices
from uuid import uuid4
from enum import Enum

# --- Enums ---

class Mode(str, Enum):
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    TEXT_IMAGE_TO_3D = "text_image_to_3d"
    REFINE_3D = "refine_3d"
    MESH_OPS = "mesh_ops"

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

# --- Common Models ---

class ImageItem(BaseModel):
    image_id: str = Field(..., min_length=1, max_length=64)
    uri: str = Field(..., min_length=3)
    role: Role
    mask_uri: Optional[str] = Field(None, min_length=3)

class SourceMesh(BaseModel):
    uri: str = Field(..., min_length=3)
    format: Optional[MeshFormat] = None

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
    texture_resolution: int
    maps: List[MapType]
    single_material: bool

class LOD(BaseModel):
    generate: bool
    levels: List[float] = Field(default_factory=list)

class Rigging(BaseModel):
    generate: bool
    type: RiggingType

class Constraints(BaseModel):
    target_formats: List[MeshFormat] = Field(..., validation_alias=AliasChoices("target_formats", "target_format")) # Support both for compatibility
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

    class Config:
        populate_by_name = True

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
    quality_report: Optional[Dict[str, Any]] = None
    error: Optional[ErrorObject] = None


# --- MeshOps Specific Models (Now safe to define) ---

class BlendImportConfig(BaseModel):
    enabled: bool = False
    scene: Optional[str] = None
    collection: Optional[str] = None
    object_names: Optional[List[str]] = None
    object_types: List[str] = ["MESH", "CURVE", "SURFACE", "FONT", "META", "GPENCIL"]
    apply_modifiers: bool = True
    modifier_evaluation: Literal["render", "viewport"] = "render"
    convert_non_mesh_to_mesh: bool = True
    triangulate_on_import: bool = False
    join_strategy: Literal["none", "by_collection", "by_material", "all"] = "none"
    include_hidden: bool = False
    use_linked_data_policy: Literal["pack", "resolve", "fail"] = "pack"
    external_assets_policy: Literal["pack", "resolve", "strip", "fail"] = "pack"
    texture_path_policy: Literal["relative", "absolute", "pack"] = "pack"
    unit_from_blend: Literal["use_scene", "override"] = "use_scene"
    axis_from_blend: Literal["use_scene", "override"] = "use_scene"

class MeshOpsSourceMesh(BaseModel):
    mesh_id: str
    uri: str
    format: str # glb, gltf, obj, blend, etc.
    name_hint: Optional[str] = None
    units_hint: Optional[ScaleUnit] = None
    axis_hint: Optional[Axis] = None
    material_policy: Literal["keep", "override", "strip"] = "keep"
    submesh_policy: Literal["keep", "merge_by_material", "merge_all"] = "keep"
    blend_import: Optional[BlendImportConfig] = None

class TextureSource(BaseModel):
    source_id: str
    uri: str
    type: Literal["single_image", "multi_view", "atlas", "tileable_set"]
    maps: List[MapType]
    mapping_hint: Literal["project", "unwrap", "triplanar"] = "project"
    mask_uri: Optional[str] = None
    weight: float = 0.0

class AuxInputs(BaseModel):
    cage_mesh_uri: Optional[str] = None
    reference_images: List[ImageItem] = Field(default_factory=list)
    texture_sources: List[TextureSource] = Field(default_factory=list)

class MeshOpsInput(BaseModel):
    source_meshes: List[MeshOpsSourceMesh]
    aux_inputs: Optional[AuxInputs] = None

class MeshOpsPreset(BaseModel):
    preset_id: str
    overrides: Optional[Dict[str, Any]] = None

class Operation(BaseModel):
    op_id: str
    type: str
    target: Dict[str, Any]
    params: Dict[str, Any] = Field(default_factory=dict)
    on_fail: Literal["stop", "skip", "partial"] = "stop"
    depends_on: List[str] = Field(default_factory=list)

class BlendPolicy(BaseModel):
    allow_blend: bool = True
    require_headless_import: bool = True
    max_import_time_ms: int = 600000

class FileSafety(BaseModel):
    disallow_external_refs: bool = True

class Naming(BaseModel):
    sanitize: bool = True
    max_len: int = 64

class AutoTexturing(BaseModel):
    enabled: bool = True
    strategy: Literal["from_images", "synthesize", "hybrid"] = "from_images"
    style_strength: float = 0.0
    detail_level: Literal["low", "medium", "high"] = "medium"
    seam_reduce: bool = True
    color_consistency: bool = True
    tileable: bool = False
    denoise: Literal["off", "light", "strong"] = "off"
    upscale: Literal["off", "2x", "4x"] = "off"

class BakingConfig(BaseModel):
    enabled: bool = True
    high_mesh_id: Optional[str] = None
    cage_uri: Optional[str] = None
    maps: List[str] = ["normal", "ao"]
    ray_distance: float = 0.0
    antialiasing: Literal["none", "2x", "4x", "8x"] = "2x"

class ChannelPacking(BaseModel):
    enabled: bool = True
    preset: Literal["orm", "rma", "none"] = "orm"
    outputs: List[Dict[str, Any]] = Field(default_factory=list)

class MeshOpsMaterials(Materials):
    # Extension of base materials with extra Ops configs
    atlas: bool = False
    auto_texturing: Optional[AutoTexturing] = None
    baking: Optional[BakingConfig] = None
    channel_packing: Optional[ChannelPacking] = None

class MeshOpsConstraints(Constraints):
    materials: Optional[MeshOpsMaterials] = None
    naming: Optional[Naming] = None
    file_safety: Optional[FileSafety] = None
    blend_policy: Optional[BlendPolicy] = None

class Engine(BaseModel):
    engine_version: Optional[str] = None
    determinism: Determinism = Determinism.BEST_EFFORT
    seed: int = 0

class MeshOpsRequest(BaseModel):
    request_id: str
    schema_version: str = "1.0"
    mode: Literal[Mode.MESH_OPS]
    engine: Optional[Engine] = None
    input: MeshOpsInput
    preset: Optional[MeshOpsPreset] = None
    operations: List[Operation] = Field(default_factory=list)
    constraints: MeshOpsConstraints
    output: Output

# --- Generation Request ---

class Input(BaseModel):
    text_prompt: Optional[str] = Field(default="")
    negative_prompt: Optional[str] = None
    images: List[ImageItem] = Field(default_factory=list)
    source_mesh: Optional[SourceMesh] = None

class Batch(BaseModel):
    enabled: bool
    items: List[Dict[str, Any]] = Field(default_factory=list)
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
