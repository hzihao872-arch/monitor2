"""Lazy offline adapter for the existing Qwen3-VL-8B-Instruct snapshot."""
import io
import os
import time
from pathlib import Path

from PIL import Image


def prepare_content(request):
    content=[{'type':'text','text':request['prompt']}]
    metas=request.get('image_meta',[{} for _ in request['images']])
    for evidence_id,data,meta in zip(request['image_ids'],request['images'],metas):
        image=Image.open(io.BytesIO(data)).convert('RGB')
        label=f'Evidence {evidence_id}'
        if meta.get('time_ms') is not None:label+=f' at {meta["time_ms"]} ms'
        if meta.get('parent_id'):label+=f', crop of {meta["parent_id"]} box {meta["crop_xyxy"]}'
        content.extend(({'type':'text','text':label+':'},
                        {'type':'image','image':image}))
    return content


class QwenBackend:
    def __init__(self,model_path,attention='flash_attention_2'):
        self.path=Path(model_path).resolve()
        self.attention=attention
        self.identity=f'qwen3-vl-8b-instruct:bfloat16:{attention}:{self.path}'
        self.model=None
        self.processor=None
        self.last_metrics=None

    def _load(self):
        if self.model is not None:
            return
        if not (self.path/'config.json').is_file():
            raise RuntimeError('existing local checkpoint required')
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WANDB_MODE='disabled')
        import torch
        from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA required for 8B adapter')
        self.processor=AutoProcessor.from_pretrained(self.path,local_files_only=True)
        self.model=Qwen3VLForConditionalGeneration.from_pretrained(
            self.path,dtype=torch.bfloat16,attn_implementation=self.attention,
            local_files_only=True).to('cuda').eval()

    def generate(self,request):
        self._load()
        import torch
        content=prepare_content(request)
        t0=time.perf_counter()
        encoded=self.processor.apply_chat_template(
            [{'role':'user','content':content}],tokenize=True,add_generation_prompt=True,
            return_dict=True,return_tensors='pt')
        input_tokens=int(encoded['input_ids'].shape[-1])
        cap_in,cap_out=request['limits']
        if input_tokens>cap_in:
            raise RuntimeError(f'input token budget exceeded: {input_tokens}>{cap_in}')
        encoded=encoded.to('cuda')
        torch.cuda.reset_peak_memory_stats()
        with torch.inference_mode():
            output=self.model.generate(**encoded,max_new_tokens=cap_out,do_sample=False)
        completion=output[:,input_tokens:]
        raw=self.processor.batch_decode(completion,skip_special_tokens=True)[0]
        torch.cuda.synchronize()
        self.last_metrics={'input_tokens':input_tokens,'output_tokens':int(completion.shape[-1]),
                           'elapsed_seconds':time.perf_counter()-t0,
                           'peak_vram_bytes':int(torch.cuda.max_memory_allocated()),
                           'hit_output_cap':int(completion.shape[-1])>=cap_out}
        return raw
