from pathlib import Path

HTML_TEMPLATE_MODEL_VIEWER = """
<!DOCTYPE html>
<html>
<head>
    <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
    <style>
        body { 
            margin: 0; 
            background: radial-gradient(circle at 50% 50%, #f9fafb 0%, #e5e7eb 100%);
            height: 100vh; 
            width: 100vw; 
            overflow: hidden; 
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        @media (prefers-color-scheme: dark) {
            body {
                background: radial-gradient(circle at 50% 50%, #1f2937 0%, #111827 100%);
            }
        }
        model-viewer { width: 100%; height: 100%; --progress-bar-color: #6366f1; }
    </style>
</head>
<body>
    <model-viewer src="#src#" 
                  alt="Hunyuan3D Model" 
                  auto-rotate 
                  camera-controls 
                  shadow-intensity="1" 
                  exposure="1.2" 
                  environment-image="neutral"
                  skybox-image=""
                  interaction-prompt="auto"
                  ar
                  ar-modes="webxr scene-viewer quick-look">
    </model-viewer>
</body>
</html>
"""

HTML_PLACEHOLDER = """
<div style='height: 100%; min-height: 550px; width: 100%; border-radius: 12px; border: 2px dashed #e5e7eb; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #f9fafb00; transition: all 0.3s ease;'>
  <div style='display: flex; justify-content: center; align-items: center; width: 64px; height: 64px; background-color: rgba(99, 102, 241, 0.1); border-radius: 50%; margin-bottom: 16px;'>
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z"></path></svg>
  </div>
  <h3 style='font-size: 18px; font-weight: 600; color: #374151; margin: 0 0 8px 0;'>Ready to Create</h3>
  <p style='font-size: 14px; color: #6b7280; margin: 0; text-align: center; max-width: 240px;'>Configure your prompt and settings on the left, then click Generate.</p>
</div>
"""

def load_css():
    try:
        css_path = Path(__file__).parent / "assets" / "theme.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return ""
    except Exception:
        return ""

CSS_STYLES = load_css()
