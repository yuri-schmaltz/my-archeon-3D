# Archeon 3D 2.0

<div align="center">
  <a href=https://3d.hunyuan.tencent.com target="_blank">Official Site</a> |
  <a href=https://huggingface.co/spaces/tencent/Hunyuan3D-2  target="_blank">HF Demo</a> |
  <a href=https://huggingface.co/tencent/Hunyuan3D-2 target="_blank">HF Models</a> |
  <a href=https://arxiv.org/abs/2501.12202 target="_blank">Technical Report</a> |
  <a href=https://discord.gg/dNBrdrGGMa target="_blank">Discord</a>
</div>

[//]: # (  <a href=# target="_blank"><img src=https://img.shields.io/badge/Report-b5212f.svg?logo=arxiv height=22px></a>)

[//]: # (  <a href=# target="_blank"><img src= https://img.shields.io/badge/Colab-8f2628.svg?logo=googlecolab height=22px></a>)

[//]: # (  <a href="#"><img alt="PyPI - Downloads" src="https://img.shields.io/pypi/v/mulankit?logo=pypi"  height=22px></a>)

<br>

<p align="center">
“ Living out everyone’s imagination on creating and manipulating 3D assets.”
</p>




## 🔥 News

- July 26, 2025: 🤗 We release the first open-source, simulation-capable, immersive 3D world generation model, [HunyuanWorld-1.0](https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0)!
- June 23, 2025: 📄 Release the system technical report of [Archeon 3D 2.5](https://arxiv.org/abs/2506.16504).
- June 13, 2025: 🤗 Release [Archeon 3D-2.1](https://github.com/Tencent-Hunyuan/Archeon 3D-2.1), fully open-sourced with new PBR model, VAE encoder, and all training code. 
- Apr 1, 2025: 🤗 Release turbo paint model [Archeon 3D-Paint-v2-0-Turbo](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-paint-v2-0-turbo), and multiview texture generation pipeline! Stay tuned for our new texture generation model [RomanTex](https://github.com/oakshy/RomanTex) and PBR material generation [MaterialMVP](https://github.com/ZebinHe/MaterialMVP/)! 
- Mar 19, 2025: 🤗 Release turbo model [Archeon 3D-2-Turbo](https://huggingface.co/tencent/Hunyuan3D-2/), [Archeon 3D-2mini-Turbo](https://huggingface.co/tencent/Hunyuan3D-2mini/) and [FlashVDM](https://github.com/Tencent/FlashVDM).
- Mar 18, 2025: 🤗 Release multiview shape model [Archeon 3D-2mv](https://huggingface.co/tencent/Hunyuan3D-2mv) and 0.6B
  shape model [Archeon 3D-2mini](https://huggingface.co/tencent/Hunyuan3D-2mini).
- Feb 14, 2025: 🛠️ Release texture enhancement module!
- Feb 3, 2025: 🐎
  Release [Archeon 3D-DiT-v2-0-Fast](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-dit-v2-0-fast), our
  guidance distillation model that could half the dit inference time.
- Jan 9, 2026: 🚀 Release **Archeon 3D-2 Pro Generator** for Blender 5.0! Includes connection diagnostics, smart object integration, and enhanced UI.
- Jan 27, 2025: 🛠️ Release Blender addon for Archeon 3D 2.0, Check it out [here](#blender-addon).
- Jan 23, 2025: 💬 We thank community members for
  creating [Windows installation tool](https://github.com/YanWenKun/Archeon 3D-2-WinPortable), ComfyUI support
  with [ComfyUI-Archeon 3DWrapper](https://github.com/kijai/ComfyUI-Archeon 3DWrapper)
  and [ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack) and other
  awesome [extensions](#community-resources).
- Jan 21, 2025: 💬 Enjoy exciting 3D generation on our website [Archeon 3D Studio](https://3d.hunyuan.tencent.com)!
- Jan 21, 2025: 🤗 Release inference code and pretrained models
  of [Archeon 3D 2.0](https://huggingface.co/tencent/Hunyuan3D-2). Please give it a try
  via [huggingface space](https://huggingface.co/spaces/tencent/Hunyuan3D-2) and
  our [official site](https://3d.hunyuan.tencent.com)!

> Join our **[Discord](https://discord.gg/dNBrdrGGMa)** group to discuss and find help from us.






## **Abstract**

We present Archeon 3D 2.0, an advanced large-scale 3D synthesis system for generating high-resolution textured 3D assets.
This system includes two foundation components: a large-scale shape generation model - Archeon 3D-DiT, and a large-scale
texture synthesis model - Archeon 3D-Paint.
The shape generative model, built on a scalable flow-based diffusion transformer, aims to create geometry that properly
aligns with a given condition image, laying a solid foundation for downstream applications.
The texture synthesis model, benefiting from strong geometric and diffusion priors, produces high-resolution and vibrant
texture maps for either generated or hand-crafted meshes.
Furthermore, we build Archeon 3D-Studio - a versatile, user-friendly production platform that simplifies the re-creation
process of 3D assets. It allows both professional and amateur users to manipulate or even animate their meshes
efficiently.
We systematically evaluate our models, showing that Archeon 3D 2.0 outperforms previous state-of-the-art models,
including the open-source models and closed-source models in geometry details, condition alignment, texture quality, and
e.t.c.



<p align="center">


## ☯️ **Archeon 3D 2.0**

### Architecture

Archeon 3D 2.0 features a two-stage generation pipeline, starting with the creation of a bare mesh, followed by the
synthesis of a texture map for that mesh. This strategy is effective for decoupling the difficulties of shape and
texture generation and also provides flexibility for texturing either generated or handcrafted meshes.

<p align="left">


### Performance

We have evaluated Archeon 3D 2.0 with other open-source as well as close-source 3d-generation methods.
The numerical results indicate that Archeon 3D 2.0 surpasses all baselines in the quality of generated textured 3D assets
and the condition following ability.

| Model                   | CMMD(⬇)   | FID_CLIP(⬇) | FID(⬇)      | CLIP-score(⬆) |
|-------------------------|-----------|-------------|-------------|---------------|
| Top Open-source Model1  | 3.591     | 54.639      | 289.287     | 0.787         |
| Top Close-source Model1 | 3.600     | 55.866      | 305.922     | 0.779         |
| Top Close-source Model2 | 3.368     | 49.744      | 294.628     | 0.806         |
| Top Close-source Model3 | 3.218     | 51.574      | 295.691     | 0.799         |
| Archeon 3D 2.0           | **3.193** | **49.165**  | **282.429** | **0.809**     |

Generation results of Archeon 3D 2.0:


## 🎁 Models Zoo

It takes 6 GB VRAM for shape generation and 16 GB for shape and texture generation in total.

Archeon 3D-2-1 Series

| Model                | Description                   | Date       | Size | Huggingface                                                                             |
|----------------------|-------------------------------|------------|------|-----------------------------------------------------------------------------------------|
| Archeon 3D-DiT-v2-1   | Mini Image to Shape Model     | 2025-06-13 | 3.0B | [Download](https://huggingface.co/tencent/Hunyuan3D-2.1/tree/main/hunyuan3d-dit-v2-1)   |
| Archeon 3D-Paint-v2-1 | Texture Generation Model    | 2025-06-13 | 1.3B | [Download](https://huggingface.co/tencent/Hunyuan3D-2.1/tree/main/hunyuan3d-paintpbr-v2-1) |

Archeon 3D-2mini Series

| Model                       | Description                   | Date       | Size | Huggingface                                                                                      |
|-----------------------------|-------------------------------|------------|------|--------------------------------------------------------------------------------------------------|
| Archeon 3D-DiT-v2-mini-Turbo | Step Distillation Version     | 2025-03-19 | 0.6B | [Download](https://huggingface.co/tencent/Hunyuan3D-2mini/tree/main/hunyuan3d-dit-v2-mini-turbo) |
| Archeon 3D-DiT-v2-mini-Fast  | Guidance Distillation Version | 2025-03-18 | 0.6B | [Download](https://huggingface.co/tencent/Hunyuan3D-2mini/tree/main/hunyuan3d-dit-v2-mini-fast)  |
| Archeon 3D-DiT-v2-mini       | Mini Image to Shape Model     | 2025-03-18 | 0.6B | [Download](https://huggingface.co/tencent/Hunyuan3D-2mini/tree/main/hunyuan3d-dit-v2-mini)       |


Archeon 3D-2mv Series

| Model                     | Description                    | Date       | Size | Huggingface                                                                                  |
|---------------------------|--------------------------------|------------|------|----------------------------------------------------------------------------------------------| 
| Archeon 3D-DiT-v2-mv-Turbo | Step Distillation Version      | 2025-03-19 | 1.1B | [Download](https://huggingface.co/tencent/Hunyuan3D-2mv/tree/main/hunyuan3d-dit-v2-mv-turbo) |
| Archeon 3D-DiT-v2-mv-Fast  | Guidance Distillation Version  | 2025-03-18 | 1.1B | [Download](https://huggingface.co/tencent/Hunyuan3D-2mv/tree/main/hunyuan3d-dit-v2-mv-fast)  |
| Archeon 3D-DiT-v2-mv       | Multiview Image to Shape Model | 2025-03-18 | 1.1B | [Download](https://huggingface.co/tencent/Hunyuan3D-2mv/tree/main/hunyuan3d-dit-v2-mv)       |

Archeon 3D-2 Series

| Model                      | Description                 | Date       | Size | Huggingface                                                                               |
|----------------------------|-----------------------------|------------|------|-------------------------------------------------------------------------------------------| 
| Archeon 3D-DiT-v2-0-Turbo   | Step Distillation Model     | 2025-03-19 | 1.1B | [Download](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-dit-v2-0-turbo)   |
| Archeon 3D-DiT-v2-0-Fast    | Guidance Distillation Model | 2025-02-03 | 1.1B | [Download](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-dit-v2-0-fast)    |
| Archeon 3D-DiT-v2-0         | Image to Shape Model        | 2025-01-21 | 1.1B | [Download](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-dit-v2-0)         |
| Archeon 3D-Paint-v2-0       | Texture Generation Model    | 2025-01-21 | 1.3B | [Download](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-paint-v2-0)       |
| Archeon 3D-Paint-v2-0-Turbo | Distillation Texure Model   | 2025-04-01 | 1.3B | [Download](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-paint-v2-0-turbo) |
| Archeon 3D-Delight-v2-0     | Image Delight Model         | 2025-01-21 | 1.3B | [Download](https://huggingface.co/tencent/Hunyuan3D-2/tree/main/hunyuan3d-delight-v2-0)     | 

## 🤗 Get Started with Archeon 3D 2.0

Archeon 3D 2.0 supports MacOS, Windows, Linux. You may follow the next steps to use Archeon 3D 2.0 via:

- [Code](#code-usage)
- [Gradio App](#gradio-app)
- [API Server](#api-server)
- [Docker Usage](docs/DOCKER.md)
- [Blender Addon](#blender-addon)
- [Official Site](#official-site)

### Install Requirements

Please install Pytorch via the [official](https://pytorch.org/) site. Then install the other requirements via:

```bash
pip install -r requirements.txt
pip install -e .
```

#### Texture Generation Extensions
```bash
# for texture
cd hy3dgen/texgen/custom_rasterizer
python3 setup.py install
cd ../../..
cd hy3dgen/texgen/differentiable_renderer
python3 setup.py install
```


### Code Usage

We designed a diffusers-like API to use our shape generation model - Archeon 3D-DiT and texture synthesis model -
Archeon 3D-Paint.

You could assess **Archeon 3D-DiT** via:

```python
from hy3dgen.shapegen import Archeon 3DDiTFlowMatchingPipeline

pipeline = Archeon 3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2')
mesh = pipeline(image='path/to/your/image.png')[0]
```

The output mesh is a [trimesh object](https://trimesh.org/trimesh.html), which you could save to glb/obj (or other format) file.
### Gradio App

You can now launch a single unified app and select the model (Normal, Multiview) directly from the UI:

```bash
```bash
# Safe default (loads models on demand, opens browser automatically)
# Safe default (loads models on demand, opens browser automatically)
python3 my_hunyuan_3d.py
```

#### New Pro Features (v2.0)
- **Unified Interface**: Full-screen, responsive layout with optimized density.
- **Stop Generation**: Immediately cancel generation tasks with the Red Stop Button.
- **Smart Tabs**: Auto-switching prompts based on model category (Multi-view/Normal).
- **Progress Feedback**: Granular, thread-safe progress bars.


### API Server

You could launch an API server locally, which you could post web request for Image/Text to 3D, Texturing existing mesh, and e.t.c.

```bash
# Default port changed to 8081 for better coexistence
python my_hunyuan_3d.py --api --host 0.0.0.0 --port 8081
```

#### Features
- **Security**: Basic Auth enabled (Default: `admin` / `admin`). Configure via `API_USERNAME` and `API_PASSWORD` env vars.
- **Diagnostics**: `/health` endpoint for connection and worker status.
- **Metrics**: Prometheus metrics available at `/metrics`.

#### Usage Example

A demo post request for image to 3D using basic authentication:

```bash
img_b64_str=$(base64 -w 0 your_image.png)
curl -X POST "http://localhost:8081/generate" \
     -u admin:admin \
     -H "Content-Type: application/json" \
     -d '{
           "image": "'"$img_b64_str"'",
           "texture": false,
           "model": "Normal"
         }' \
     -o output.glb
```

### Blender Addon

With an API server launched, you can use our **Archeon 3D-2 Pro (v1.3)** addon for a seamless 3D workflow inside Blender.

- **Download**: [scripts/blender_addon.py](scripts/blender_addon.py)
- **Compatibility**: Fully compatible with **Blender 5.0** and earlier versions.
- **Pro Features**:
  - **Connection Diagnostics**: Test API reachability directly from the panel.
  - **Smart Context**: Automatically switches between *Generation* and *Texturing* based on object selection.
  - **Transform Sync**: Inherit position/rotation/scale from existing scene objects.
  - **Auto-Organization**: Collections for keeping your workspace clean.



### Official Site

Don't forget to visit [Archeon 3D](https://3d.hunyuan.tencent.com) for quick use, if you don't want to host yourself.

## 📑 Open-Source Plan

- [x] Inference Code
- [x] Model Checkpoints
- [x] Technical Report
- [x] ComfyUI
- [x] Finetuning
- [ ] TensorRT Version

## 🛠️ Development

We use `pytest` for ensuring the reliability of the Request Manager and Inference pipeline.

```bash
# Run all tests
pytest tests/
```

## 🔗 BibTeX

If you found this repository helpful, please cite our reports:

```bibtex
@misc{lai2025hunyuan3d25highfidelity3d,
      title={Archeon 3D 2.5: Towards High-Fidelity 3D Assets Generation with Ultimate Details}, 
      author={Tencent Archeon 3D Team},
      year={2025},
      eprint={2506.16504},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2506.16504}, 
}

@misc{hunyuan3d22025tencent,
    title={Archeon 3D 2.0: Scaling Diffusion Models for High Resolution Textured 3D Assets Generation},
    author={Tencent Archeon 3D Team},
    year={2025},
    eprint={2501.12202},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}

@misc{yang2024hunyuan3d,
    title={Archeon 3D 1.0: A Unified Framework for Text-to-3D and Image-to-3D Generation},
    author={Tencent Archeon 3D Team},
    year={2024},
    eprint={2411.02293},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}
```

## Community Resources

Thanks for the contributions of community members, here we have these great extensions of Archeon 3D 2.0:

- [ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack)
- [ComfyUI-Archeon 3DWrapper](https://github.com/kijai/ComfyUI-Archeon 3DWrapper)
- [Archeon 3D-2-for-windows](https://github.com/sdbds/Archeon 3D-2-for-windows)
- [📦 A bundle for running on Windows](https://github.com/YanWenKun/Archeon 3D-2-WinPortable)
- [Archeon 3D-2GP](https://github.com/deepbeepmeep/Archeon 3D-2GP)
- [Kaggle Notebook](https://github.com/darkon12/Archeon 3D-2GP_Kaggle)

## Acknowledgements

We would like to thank the contributors to
the [Trellis](https://github.com/microsoft/TRELLIS),  [DINOv2](https://github.com/facebookresearch/dinov2), [Stable Diffusion](https://github.com/Stability-AI/stablediffusion), [FLUX](https://github.com/black-forest-labs/flux), [diffusers](https://github.com/huggingface/diffusers), [HuggingFace](https://huggingface.co), [CraftsMan3D](https://github.com/wyysf-98/CraftsMan3D),
and [Michelangelo](https://github.com/NeuralCarver/Michelangelo/tree/main) repositories, for their open research and
exploration.

## Star History

<a href="https://star-history.com/#Tencent/Archeon 3D-2&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Tencent/Archeon 3D-2&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Tencent/Archeon 3D-2&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Tencent/Archeon 3D-2&type=Date" />
 </picture>
</a>
