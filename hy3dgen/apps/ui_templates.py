HTML_TEMPLATE_MODEL_VIEWER = """
<!DOCTYPE html>
<html>
<head>
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
    <style>
        body { margin: 0; background-color: #ffffff; height: 100vh; width: 100vw; overflow: hidden; }
        model-viewer { width: 100%; height: 100%; --progress-bar-color: #4f46e5; }
    </style>
</head>
<body>
    <model-viewer src="#src#" 
                  alt="Hunyuan3D Model" 
                  auto-rotate 
                  camera-controls 
                  shadow-intensity="1" 
                  exposure="1" 
                  interaction-prompt="auto">
    </model-viewer>
</body>
</html>
"""

HTML_PLACEHOLDER = """
<div style='height: 100%; min-height: 550px; width: 100%; border-radius: 8px; border-color: #e5e7eb; border-style: solid; border-width: 1px; display: flex; justify-content: center; align-items: center;'>
  <div style='text-align: center; font-size: 16px; color: #6b7280;'>
    <p style="color: #6b7280; font-weight: bold;">Ready to Generate</p>
    <p style="color: #8d8d8d;">Your 3D model will appear here.</p>
  </div>
</div>

"""

CSS_STYLES = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    .gradio-container { font-family: 'Inter', system-ui, sans-serif !important; min-height: 0 !important; }
    
    .app.svelte-wpkpf6.svelte-wpkpf6:not(.fill_width) { max-width: 100% !important; padding: 0 20px; }
    
    #tab_img_prompt { padding: 0 !important; }
    #tab_txt_prompt { padding: 0 !important; }
    #tab_mv_prompt { padding: 0 !important; }
    
    /* Buttons */
    button.primary { 
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important; 
        border: none !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease;
    }
    button.primary:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    
    /* Model Viewer Integration */
    .mv-image button .wrap { font-size: 10px; }
    .mv-image .icon-wrap { width: 20px; }
    
    /* Output Refresh */
    iframe { width: 100% !important; }
"""
