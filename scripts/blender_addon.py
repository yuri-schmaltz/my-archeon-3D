# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
# except for the third-party components listed below.
# Hunyuan 3D does not impose any additional limitations beyond what is outlined
# in the repsective licenses of these third-party components.
# Users must comply with all terms and conditions of original licenses of these third-party
# components and must ensure that the usage of the third party components adheres to
# all relevant laws and regulations.

# For avoidance of doubts, Hunyuan 3D means the large language models and
# their software and algorithms, including trained model weights, parameters (including
# optimizer states), machine-learning model code, inference-enabling code, training-enabling code,
# fine-tuning enabling code and other elements of the foregoing made publicly available
# by Tencent in accordance with TENCENT HUNYUAN COMMUNITY LICENSE AGREEMENT.

bl_info = {
    "name": "Hunyuan3D-2 Pro Generator",
    "author": "Tencent Hunyuan3D & Antigravity Editor",
    "version": (1, 3),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Hunyuan3D-2",
    "description": "Professional 3D generation with Blender 5.0 compatibility",
    "category": "3D View",
}
import base64
import os
import tempfile
import threading

import bpy
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty


class Hunyuan3DProperties(bpy.types.PropertyGroup):
    prompt: StringProperty(
        name="Text Prompt",
        description="Describe what you want to generate",
        default=""
    )
    api_url: StringProperty(
        name="API URL",
        description="URL of the Text-to-3D API service",
        default="http://localhost:8081"
    )
    api_username: StringProperty(
        name="Username",
        description="API Basic Auth Username",
        default="admin"
    )
    api_password: StringProperty(
        name="Password",
        description="API Basic Auth Password",
        default="admin",
        subtype='PASSWORD'
    )
    api_timeout: IntProperty(
        name="Timeout (s)",
        description="Timeout for API requests",
        default=300,
        min=10,
        max=3600
    )
    is_processing: BoolProperty(
        name="Processing",
        default=False
    )
    job_id: StringProperty(
        name="Job ID",
        default=""
    )
    status_message: StringProperty(
        name="Status Message",
        default=""
    )
    # Add image path property
    image_path: StringProperty(
        name="Image",
        description="Select an image to upload",
        subtype='FILE_PATH'
    )
    # Modified octree_resolution property
    octree_resolution: IntProperty(
        name="Octree Resolution",
        description="Octree resolution for the 3D generation",
        default=256,
        min=128,
        max=512,
    )
    num_inference_steps: IntProperty(
        name="Number of Inference Steps",
        description="Number of inference steps for the 3D generation",
        default=20,
        min=20,
        max=50
    )
    guidance_scale: FloatProperty(
        name="Guidance Scale",
        description="Guidance scale for the 3D generation",
        default=5.5,
        min=1.0,
        max=10.0
    )
    # Add texture property
    texture: BoolProperty(
        name="Generate Texture",
        description="Whether to generate texture for the 3D model",
        default=False
    )
    # Advanced Import Options
    auto_center: BoolProperty(
        name="Auto Center",
        description="Automatically center the imported mesh",
        default=True
    )
    match_transform: BoolProperty(
        name="Match Selected",
        description="Match location/rotation/scale of selected object",
        default=True
    )
    import_collection: StringProperty(
        name="Collection",
        description="Import models into this collection",
        default="Hunyuan3D_Output"
    )
    model_category: bpy.props.EnumProperty(
        name="Model",
        description="Select the engine capacity",
        items=[
            ('Normal', 'Normal (1.1B)', 'Standard balanced model'),
            ('Small', 'Small (0.6B)', 'Lightweight fast model'),
            ('Multiview', 'Multiview (1.1B)', 'Specialized multiview model'),
        ],
        default='Normal'
    )


class Hunyuan3DTestConnectionOperator(bpy.types.Operator):
    bl_idname = "object.hunyuan3d_test_connection"
    bl_label = "Test Connection"
    bl_description = "Check if the API server is reachable"

    def execute(self, context):
        props = context.scene.gen_3d_props
        base_url = props.api_url.rstrip('/')
        auth = (props.api_username, props.api_password)
        
        try:
            # We try the /health endpoint first
            response = requests.get(f"{base_url}/health", auth=auth, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.report({'INFO'}, f"Connected! Worker: {data.get('worker_id', 'unknown')}")
                props.status_message = "Connection: OK"
            else:
                self.report({'ERROR'}, f"Auth failed or endpoint missing (Status: {response.status_code})")
                props.status_message = f"Connection Error: {response.status_code}"
        except Exception as e:
            self.report({'ERROR'}, f"Connection failed: {str(e)}")
            props.status_message = "Connection: Failed"
        
        return {'FINISHED'}


class Hunyuan3DOperator(bpy.types.Operator):
    bl_idname = "object.generate_3d"
    bl_label = "Generate 3D Model"
    bl_description = "Generate a 3D model from text description, an image or a selected mesh"

    job_id = ''
    prompt = ""
    api_url = ""
    image_path = ""
    octree_resolution = 256
    num_inference_steps = 20
    guidance_scale = 5.5
    texture = False  # New property
    selected_mesh_base64 = ""
    model_category = "Normal"
    selected_mesh = None  # New property, for storing selected mesh

    thread = None
    task_finished = False
    error_occurred = False
    error_message = ""

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            props = context.scene.gen_3d_props
            props.is_processing = False
            props.status_message = "Cancelled by user"
            return {'CANCELLED'}

        if self.task_finished:
            self.task_finished = False
            props = context.scene.gen_3d_props
            props.is_processing = False
            
            if self.error_occurred:
                self.report({'ERROR'}, f"Hunyuan3D Error: {self.error_message}")
                props.status_message = f"Error: {self.error_message}"
            else:
                self.report({'INFO'}, "Hunyuan3D: Generation completed successfully")
                props.status_message = "Status: Completed"
            
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        props = context.scene.gen_3d_props
        
        # Pre-flight checks
        if props.prompt == "" and props.image_path == "":
            self.report({'WARNING'}, "Please provide at least a text prompt or an image.")
            return {'CANCELLED'}
            
        # Capture parameters
        self.api_url = props.api_url.rstrip('/')
        self.auth = (props.api_username, props.api_password)
        self.timeout = props.api_timeout
        self.prompt = props.prompt
        self.image_path = bpy.path.abspath(props.image_path)
        self.octree_resolution = props.octree_resolution
        self.num_inference_steps = props.num_inference_steps
        self.guidance_scale = props.guidance_scale
        self.texture = props.texture
        self.model_category = props.model_category
        
        # Import settings
        self.auto_center = props.auto_center
        self.match_transform = props.match_transform
        self.collection_name = props.import_collection

        # Context detection
        self.selected_mesh = context.active_object if context.active_object and context.active_object.type == 'MESH' else None
        self.selected_mesh_base64 = ""

        if self.selected_mesh:
            try:
                temp_glb = tempfile.NamedTemporaryFile(delete=False, suffix=".glb")
                temp_glb.close()
                
                # Robust export for newer Blender versions
                if hasattr(bpy.ops.export_scene, "gltf"):
                    bpy.ops.export_scene.gltf(filepath=temp_glb.name, use_selection=True)
                elif hasattr(bpy.ops.wm, "gltf_export"):
                    bpy.ops.wm.gltf_export(filepath=temp_glb.name, export_selected=True)
                else:
                    raise Exception("No glTF exporter found in this Blender version")

                with open(temp_glb.name, "rb") as f:
                    self.selected_mesh_base64 = base64.b64encode(f.read()).decode()
                os.unlink(temp_glb.name)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to export selected mesh: {str(e)}")
                return {'CANCELLED'}

        props.is_processing = True
        self.task_finished = False
        self.error_occurred = False
        
        # Update status
        mode_str = "Texturing" if (self.selected_mesh and self.texture) else "Generating"
        input_str = "Image" if self.image_path else "Text"
        props.status_message = f"Status: {mode_str} from {input_str}..."

        # Start thread
        self.thread = threading.Thread(target=self.work_thread, args=[context])
        self.thread.start()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def work_thread(self, context):
        try:
            payload = {
                "octree_resolution": self.octree_resolution,
                "num_inference_steps": self.num_inference_steps,
                "guidance_scale": self.guidance_scale,
                "texture": self.texture,
                "model": self.model_category
            }
            
            if self.selected_mesh_base64:
                payload["mesh"] = self.selected_mesh_base64
            
            if self.image_path and os.path.exists(self.image_path):
                with open(self.image_path, "rb") as f:
                    payload["image"] = base64.b64encode(f.read()).decode()
            
            if self.prompt:
                payload["text"] = self.prompt

            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                auth=self.auth,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self.error_occurred = True
                self.error_message = f"HTTP {response.status_code}: {response.text}"
                return

            # Save result to temp file
            temp_result = tempfile.NamedTemporaryFile(delete=False, suffix=".glb")
            temp_result.write(response.content)
            temp_result.close()

            # Schedule import in main thread
            def import_callback():
                try:
                    # Handle Collection
                    col = bpy.data.collections.get(self.collection_name)
                    if not col:
                        col = bpy.data.collections.new(self.collection_name)
                        bpy.context.scene.collection.children.link(col)
                    
                    # Set active collection to target
                    layer_col = bpy.context.view_layer.layer_collection.children.get(self.collection_name)
                    if layer_col:
                        bpy.context.view_layer.active_layer_collection = layer_col

                    # Robust import for newer Blender versions
                    if hasattr(bpy.ops.import_scene, "gltf"):
                        bpy.ops.import_scene.gltf(filepath=temp_result.name)
                    elif hasattr(bpy.ops.wm, "gltf_import"):
                        bpy.ops.wm.gltf_import(filepath=temp_result.name)
                    else:
                        raise Exception("No glTF importer found in this Blender version")

                    # Force update for Blender 5.0 scene graph
                    bpy.context.view_layer.update()
                    
                    imported_objs = [obj for obj in bpy.context.selected_objects]
                    
                    if imported_objs:
                        new_obj = imported_objs[0]
                        
                        # Smart transformation
                        if self.match_transform and self.selected_mesh:
                            new_obj.location = self.selected_mesh.location
                            new_obj.rotation_euler = self.selected_mesh.rotation_euler
                            new_obj.scale = self.selected_mesh.scale
                            
                            # Hide original
                            self.selected_mesh.hide_set(True)
                        elif self.auto_center:
                            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                            new_obj.location = (0, 0, 0)

                    os.unlink(temp_result.name)
                except Exception as e:
                    print(f"Hunyuan3D Import Error: {str(e)}")
                return None

            bpy.app.timers.register(import_callback)

        except requests.exceptions.Timeout:
            self.error_occurred = True
            self.error_message = f"Request timed out after {self.timeout}s"
        except Exception as e:
            self.error_occurred = True
            self.error_message = str(e)
        finally:
            self.task_finished = True


class Hunyuan3DPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Hunyuan3D-2'
    bl_label = 'Hunyuan3D-2 3D Generator'

    def draw(self, context):
        layout = self.layout
        props = context.scene.gen_3d_props

        if not HAS_REQUESTS:
            box = layout.box()
            box.alert = True
            box.label(text="Missing dependency: 'requests'", icon='ERROR')
            box.label(text="Please install it in Blender's Python.")
            return

        # --- Connection Section ---
        box = layout.box()
        box.label(text="Server Connection", icon='WORLD')
        box.prop(props, "api_url")
        
        row = box.row(align=True)
        row.prop(props, "api_username")
        row.prop(props, "api_password")
        
        box.operator("object.hunyuan3d_test_connection", icon='CONNECTION')

        # --- Input Section ---
        box = layout.box()
        box.label(text="Input Data", icon='IMPORT')
        box.prop(props, "prompt", icon='WORDPREVIEW')
        box.prop(props, "image_path", icon='IMAGE_DATA')
        
        # Context Awareness Info
        selected_obj = context.active_object
        if selected_obj and selected_obj.type == 'MESH':
            box.label(text=f"Target: {selected_obj.name}", icon='MESH_DATA')
        else:
            box.label(text="Mode: New Shape Generation", icon='MESH_CUBE')

        # --- Settings Section ---
        box = layout.box()
        box.label(text="Generation Settings", icon='MODIFIER')
        box.prop(props, "model_category")
        box.prop(props, "texture", icon='TEXTURE')
        
        col = box.column(align=True)
        col.prop(props, "octree_resolution")
        col.prop(props, "num_inference_steps")
        col.prop(props, "guidance_scale")

        # --- Import Section ---
        box = layout.box()
        box.label(text="Import Options", icon='OUTLINER_OB_MESH')
        box.prop(props, "import_collection", icon='GROUP')
        row = box.row()
        row.prop(props, "auto_center")
        row.prop(props, "match_transform")

        # --- Action Section ---
        layout.separator()
        row = layout.row(align=False)
        row.scale_y = 1.5
        row.enabled = not props.is_processing
        row.operator("object.generate_3d", icon='PLAY', text="Generate 3D Asset")

        if props.is_processing:
            box = layout.box()
            box.label(text="Job Status", icon='INFO')
            if props.status_message:
                for line in props.status_message.split("\n"):
                    box.label(text=line)
            else:
                box.label(text="In Progress...")


classes = (
    Hunyuan3DProperties,
    Hunyuan3DTestConnectionOperator,
    Hunyuan3DOperator,
    Hunyuan3DPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gen_3d_props = bpy.props.PointerProperty(type=Hunyuan3DProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gen_3d_props


if __name__ == "__main__":
    register()
