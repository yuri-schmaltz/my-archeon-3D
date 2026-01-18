# Archeon 3D Internationalization

_current_lang = "en"

_translations = {
    "en": {
        "app_title": "Archeon 3D Pro",
        "tab_img_prompt": "Image Prompt",
        "tab_mv_prompt": "MultiView Prompt",
        "tab_text_prompt": "Text Prompt",
        "lbl_image": "Image",
        "lbl_front": "Front 📸",
        "lbl_back": "Back 🔙",
        "lbl_left": "Left ⬅️",
        "lbl_right": "Right ➡️",
        "ph_text_prompt": "HunyuanDiT will be used to generate image.",
        "ph_negative_prompt": "Low quality, distortion, etc.",
        "lbl_gen_mode": "Generation Mode",
        "lbl_steps": "Inference Steps",
        "info_steps": "Quality vs Speed (Default: 50)",
        "lbl_guidance": "Guidance",
        "lbl_seed": "Seed",
        "lbl_rembg": "Remove Background",
        "lbl_octree": "Octree Resolution",
        "lbl_chunks": "Chunks",
        "btn_generate": "Generate 3D Model",
        "btn_stop": "Stop Generation",
        "lbl_output": "Generated Mesh",
        "footer_text": "**Archeon 3D Pro** v2.0 | Tencent Hunyuan-3D Engine | Antigravity AI Powered"
    },
    "pt": {
        "app_title": "Archeon 3D Pro",
        "tab_img_prompt": "Prompt de Imagem",
        "tab_mv_prompt": "Prompt Multi-Vista",
        "tab_text_prompt": "Prompt de Texto",
        "lbl_image": "Imagem",
        "lbl_front": "Frente 📸",
        "lbl_back": "Trás 🔙",
        "lbl_left": "Esquerda ⬅️",
        "lbl_right": "Direita ➡️",
        "ph_text_prompt": "HunyuanDiT será usado para gerar a imagem.",
        "ph_negative_prompt": "Baixa qualidade, distorção, etc.",
        "lbl_gen_mode": "Modo de Geração",
        "lbl_steps": "Passos de Inferência",
        "info_steps": "Qualidade vs Velocidade (Padrão: 50)",
        "lbl_guidance": "Guidance",
        "lbl_seed": "Seed",
        "lbl_rembg": "Remover Fundo",
        "lbl_octree": "Resolução Octree",
        "lbl_chunks": "Chunks",
        "btn_generate": "Gerar Modelo 3D",
        "btn_stop": "Parar Geração",
        "lbl_output": "Malha Gerada",
        "footer_text": "**Archeon 3D Pro** v2.0 | Tencent Hunyuan-3D Engine | Antigravity AI Powered"
    },
    "zh": {
        "app_title": "Archeon 3D Pro",
        "tab_img_prompt": "图片提示",
        "tab_mv_prompt": "多视角提示",
        "tab_text_prompt": "文本提示",
        "lbl_image": "图片",
        "lbl_front": "前视图 📸",
        "lbl_back": "后视图 🔙",
        "lbl_left": "左视图 ⬅️",
        "lbl_right": "右视图 ➡️",
        "ph_text_prompt": "使用 HunyuanDiT 生成图像。",
        "ph_negative_prompt": "低质量，变形等。",
        "lbl_gen_mode": "生成模式",
        "lbl_steps": "推理步数",
        "info_steps": "质量与速度 (默认: 50)",
        "lbl_guidance": "引导系数",
        "lbl_seed": "随机种子",
        "lbl_rembg": "移除背景",
        "lbl_octree": "八叉树分辨率",
        "lbl_chunks": "块数",
        "btn_generate": "生成 3D 模型",
        "btn_stop": "停止生成",
        "lbl_output": "生成的网格",
        "footer_text": "**Archeon 3D Pro** v2.0 | Tencent Hunyuan-3D Engine | Antigravity AI Powered"
    }
}

def set_language(lang_code):
    global _current_lang
    if lang_code in _translations:
        _current_lang = lang_code

def get(key, default=None):
    return _translations.get(_current_lang, {}).get(key, default or key)
