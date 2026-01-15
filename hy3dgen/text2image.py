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

import os
import random

import numpy as np
import torch
from diffusers import AutoPipelineForText2Image


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    os.environ["PL_GLOBAL_SEED"] = str(seed)


class HunyuanDiTPipeline:
    def __init__(
        self,
        model_path="Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled",
        device='cuda',
        low_vram_mode=False
    ):
        self.device = device
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_path,
            dtype=torch.float16,
            enable_pag=True,
            pag_applied_layers=["blocks.(16|17|18|19)"]
        )
        if low_vram_mode:
            self.pipe.enable_model_cpu_offload(device=device)
        else:
            self.pipe.to(device)
        self.pos_txt = ", white background, 3D style, best quality"
        self.neg_txt = "lowres, text, error, cropped, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"

    def compile(self):
        # accelerate hunyuan-dit transformer, first inference will cost long time
        torch.set_float32_matmul_precision('high')
        self.pipe.transformer = torch.compile(self.pipe.transformer, fullgraph=True)
        # self.pipe.vae.decode = torch.compile(self.pipe.vae.decode, fullgraph=True)
        generator = torch.Generator(device=self.pipe.device)  # infer once for hot-start
        out_img = self.pipe(
            prompt='Sailor Moon',
            negative_prompt='blurry',
            num_inference_steps=25,
            pag_scale=1.3,
            width=1024,
            height=1024,
            generator=generator,
            return_dict=False
        )[0][0]

    @torch.no_grad()
    def __call__(self, prompt, negative_prompt=None, seed=0, num_inference_steps=25):
        seed_everything(seed)
        generator = torch.Generator(device=self.pipe.device)
        generator = generator.manual_seed(int(seed))
        
        # logical handling: if negative_prompt is None, use default.
        # if prompt doesn't have "3D style", maybe append it? 
        # For now, we trust the caller (Orchestrator) to provide the full qualified prompt.
        # But we keep the original logic as fallback if needed, or just append pos_txt if not present.
        # Actually, per plan, we want to remove the hardcoded append if possible, or make it cleaner.
        # The plan said: prompt = prompt + ", " + self.pos_txt. 
        # But for full control, we should ideally let the user decide. 
        # Let's stick to the plan: remove truncation, keep appending pos_txt for safety unless we want pure raw.
        # The user Plan said: "DEPOIS: prompt=prompt + ", " + self.pos_txt (ou controle total via argumento)"
        # Let's give control. 
        
        final_prompt = prompt
        # We append pos_txt only if it's not likely already there (naive check) or just always append 
        # since it contains "white background".
        # However, the Senior Prompt already specifies "white background".
        # Let's append it to be safe but simpler.
        final_prompt = f"{prompt}, {self.pos_txt}"
        
        final_neg = negative_prompt if negative_prompt is not None else self.neg_txt

        out_img = self.pipe(
            prompt=final_prompt,
            negative_prompt=final_neg,
            num_inference_steps=num_inference_steps,
            pag_scale=1.3,
            width=1024,
            height=1024,
            generator=generator,
            return_dict=False
        )[0][0]
        return out_img
