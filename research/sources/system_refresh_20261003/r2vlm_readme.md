# [CVPR 26] Recurrent Reasoning with Vision-Language Models for Estimating Long-Horizon Embodied Task Progress

<p align="center">
        📑 <a href="https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_Recurrent_Reasoning_with_Vision-Language_Models_for_Estimating_Long-Horizon_Embodied_Task_CVPR_2026_paper.html">Paper</a> &nbsp&nbsp | &nbsp&nbsp 🤗 <a href="https://huggingface.co/collections/zhangyuelin/r2vlm">Model & Data</a> 
<br>

</p>


![Model Framework](assets/ModelFramework.png)

We propose R<sup>2</sup>VLM, **R**ecurrent **R**easoning **V**ision-**L**anguage **M**odel for long-horizon embodied task progress estimation.


## Training

We leverage [LLaMA-Factory](https://github.com/hiyouga/LlamaFactory/tree/845af89ea4a8ee4003d72de1cbddbe85910c37df) for supervised fine-tuning and [verl](https://github.com/volcengine/verl/tree/8fdc4d3f202f41461f4de9f42a637228e342668b) for reinforcement learning. To support our data format, we modify the multi-turn rollout algorithm in verl by removing historical contexts from previous turns and introducing history chain-of-thought reasoning. Our modified verl code is available at [dhcpack/verl-0.5.0-r2vlm](https://github.com/dhcpack/verl-0.5.0-r2vlm).

You can obtain the training code by cloning the submodules:

```bash
git submodule update --init --recursive
```

These two training frameworks are tracked in this repository as Git submodules under `code/framework/`:

- `code/framework/LLaMA-Factory`
- `code/framework/verl`

Please refer to the requirements of the corresponding training frameworks for installation. After setting up both frameworks, you can train R<sup>2</sup>VLM using [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) as the base model.

## Pretrained weights

We release both SFT and RL models trained on the Alfred progress estimation dataset. Training was conducted on 8·A100.

| Model | Base Model | Training Stage | Link | Training Time
| --- | --- | --- | --- | --- |
| R2VLM-Alfred-SFT | Qwen2.5-VL-7B | SFT | [Hugging Face](https://huggingface.co/zhangyuelin/R2VLM-Alfred-SFT) | 50 hours |
| R2VLM-Alfred-RL | R2VLM-Alfred-SFT | RL | [Hugging Face](https://huggingface.co/zhangyuelin/R2VLM-Alfred-RL) | 75 hours |

## Datasets

We release the Alfred progress estimation dataset at [zhangyuelin/alfred_progress_data](https://huggingface.co/datasets/zhangyuelin/alfred_progress_data). The SFT split includes cold-start chain-of-thought annotations generated with Qwen2.5-VL-72B.

The corresponding video data should be obtained from the official Alfred repository: [askforalfred/alfred](https://github.com/askforalfred/alfred).


## Benchmarks

We release the Alfred benchmark at [zhangyuelin/alfred_progress_bench](https://huggingface.co/datasets/zhangyuelin/alfred_progress_bench).

## Citation

If you find our work helpful, please cite as:

```
@InProceedings{zhang2026recurrent,
    author    = {Zhang, Yuelin and Cheng, Sijie and Li, Chen and Li, Zongzhao and Huang, Yuxin and Liu, Yang and Huang, Wenbing},
    title     = {Recurrent Reasoning with Vision-Language Models for Estimating Long-Horizon Embodied Task Progress},
    booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
    month     = {June},
    year      = {2026},
    pages     = {41150-41159}
}
```
