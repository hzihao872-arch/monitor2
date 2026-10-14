---
license: mit
modalities:
- image
- video
- tabular
- text
task_categories:
- visual-question-answering
- robotics
language:
- en
tags:
- hdf5
---

# **ViFailback Dataset: Real-World Robotic Manipulation Failure Dataset with Visual Symbol Guidance**

<p align="center">
  <a href="https://x1nyuzhou.github.io/vifailback.github.io/">
    <img src="https://img.shields.io/badge/Project-Page-4285F4?logo=googlechrome&logoColor=white" alt="Project Page">
  </a>
  <a href="https://arxiv.org/abs/2512.02787">
    <img src="https://img.shields.io/badge/arXiv-2512.02787-b31b1b?logo=arxiv&logoColor=white" alt="arXiv">
  </a>
  <a href="https://huggingface.co/sii-rhos-ai/ViFailback-8B">
    <img src="https://img.shields.io/badge/🤗_Model-ViFailback--8B-ffc107" alt="HuggingFace Model">
  </a>
  <a href="https://huggingface.co/datasets/sii-rhos-ai/vifailback-dataset-lerobot">
    <img src="https://img.shields.io/badge/🤗_LeRobot-vifailback--dataset--lerobot-ffc107" alt="HuggingFace Dataset">
  </a>
  <a href="https://github.com/x1nyuzhou/ViFailback">
    <img src="https://img.shields.io/badge/GitHub-Code-181717?logo=github&logoColor=white" alt="GitHub">
  </a>
</p>
A real-world dataset for diagnosing, correcting, and learning from robotic manipulation failures via visual symbols.

ViFailback is a large-scale, real-world robotic manipulation failure dataset introduced in the <strong style="color:red;">CVPR 2026</strong> paper **"Diagnose, Correct, and Learn from Manipulation Failures via Visual Symbols"**. It introduces **visual symbols** as an efficient interface for failure diagnosis and recovery-oriented learning.

## **🚀 Highlights**
* 🤗 A ready-to-use [LeRobot v2.1 conversion](https://huggingface.co/datasets/sii-rhos-ai/vifailback-dataset-lerobot) is available for robot learning and failure-aware policy training.
* **5,202** real-world manipulation trajectories.  
* **58,128** high-quality VQA pairs.  
* **100** distinct manipulation tasks.  
* **4** major failure categories.  
* Features **ViFailback-Bench** (Lite & Hard) and the finetuned **ViFailback-8B** VLM.

## **📊 Dataset Statistics**

![Dataset Statistics](assets/dataset_stats.png)

* **Total trajectories**: 5,202 (Successful: 657 | Failed: 4,545)  
* **Total VQA pairs**: 58,128  
* **Tasks**: 100 (including place, pull, transfer, pour, etc.)  
* **Platform**: ALOHA dual-arm robot platform.

### **Failure Taxonomy**

| Type | Description | % |
| :---- | :---- | :---- |
| **Task Planning** | Errors in the high-level task plan. | 12.40% |
| **Gripper 6D-Pose** | The gripper fails to reach its correct position or orientation. | 53.27% |
| **Gripper State** | The gripper does not close or open properly, or its level of closure or opening is insufficient. | 18.99% |
| **Human Intervention** | Disruptions from external forces that prevent task continuation. | 2.71% |

## **🎨 Visual Symbols & Correction Guidance**

ViFailback utilizes **7 visual symbols** to provide interpretable corrective guidance.

| Category | Symbol |
| :---- | :---- |
| **Motion** | **Colored Arrow** |
|  | **Circular Arrow** |
| **Spatial** | **Dual Crosshairs** |
|  | **Crosshair** |
| **State** | **ON/OFF Labels** |
|  | **Prohibition** |
|  | **Rewind** |

## **🏆 ViFailback-Bench**

![ViFailback Bench](assets/vifailback_bench.png)

### **ViFailback-Bench Lite (Closed-ended)**

Evaluates core capabilities: Failure Detection, Keyframe/Subtask Localization, Type Identification, and Low-level Avoidance/Correction.

### **ViFailback-Bench Hard (Open-ended)**

Evaluates deep reasoning: Failure Reason, High-level Avoidance/Correction, and Low-level Avoidance/Correction (CoT).

## **📂 Data Format (HDF5)**

Each episode\_X.hdf5 file structure:

episode\_X.hdf5  
├── action                        \# Target joint positions (qpos at t+1)  
├── action\_eef                    \# Target EEF pose (Puppet arm, 16d)  
├── action\_leader                 \# Master arm joint positions  
├── base\_action                   \# Base movement commands (2d)  
└── observations  
    ├── qpos       \# Current Puppet arm joint states (14d)  
    ├── qvel          
    ├── effort         
    ├── images                    \# Compressed RGB (cam\_high, cam\_left\_wrist, cam\_right\_wrist)  
    └── images\_depth              \# Raw Depth

### **Vector Mapping**

* **Joint Space (14D)**: Left Arm \[0:7\] (Joint 1-6 \+ Gripper) | Right Arm \[7:14\] (Joint 1-6 \+ Gripper).  
* **EEF Space (16D)**: Left Arm \[0:8\] (x,y,z,rx,ry,rz,rw,Gripper) | Right Arm \[8:16\] (x,y,z,rx,ry,rz,rw,Gripper).

## **⚠️ Hardware Note: Dabai Camera**

\[\!CAUTION\] RGB images and depth maps from **Dabai** cameras are **not spatially aligned**. Please perform alignment preprocessing before using them for RGB-D fusion or point cloud generation.

## **🛠 Quick Start**

```python
# Required libraries: h5py, numpy, opencv-python, tqdm, rich
import os
import numpy as np
import cv2
import h5py
import argparse
from tqdm import tqdm
from rich.console import Console
from rich.panel import Panel

# Initialize rich console for professional terminal output
console = Console()

def load_camera_data(hdf5_path, load_depth=False):
    """
    Load RGB and Depth datasets from an HDF5 file.
    
    Args:
        hdf5_path (str): Path to the target HDF5 file.
        load_depth (bool): Flag to enable/disable depth data retrieval.
        
    Returns:
        dict: A dictionary mapping stream names to their respective data arrays.
    """
    camera_names = ['cam_high', 'cam_left_wrist', 'cam_right_wrist']
    data_dict = {}
    
    try:
        with h5py.File(hdf5_path, 'r') as f:
            for cam in camera_names:
                # Load RGB image data
                rgb_key = f'observations/images/{cam}'
                if rgb_key in f:
                    data_dict[cam] = f[rgb_key][()]
                
                # Load Depth data if requested
                if load_depth:
                    depth_key = f'observations/images_depth/{cam}'
                    if depth_key in f:
                        data_dict[f"{cam}_depth"] = f[depth_key][()]
    except Exception as e:
        console.print(f"[bold red]Failed to read HDF5 {hdf5_path}:[/bold red] {e}")
    return data_dict

def save_videos(data_dict, fps, base_output_dir, rel_path, episode_name):
    """
    Process image sequences and export to categorized 'rgb' and 'depth' subdirectories.
    
    Args:
        data_dict (dict): Dictionary containing the image/depth arrays.
        fps (float): Video frame rate.
        base_output_dir (str): The root output directory specified by the user.
        rel_path (str): The relative path of the task folder.
        episode_name (str): Name of the episode (hdf5 filename without extension).
    """
    for stream_name, frames in data_dict.items():
        if frames is None or len(frames) == 0:
            continue

        is_depth = "depth" in stream_name
        
        # Determine the target directory (rgb/ or depth/)
        sub_folder_type = "depth" if is_depth else "rgb"
        final_dir = os.path.normpath(os.path.join(base_output_dir, sub_folder_type, rel_path))
        os.makedirs(final_dir, exist_ok=True)
        
        try:
            # Determine dimensions based on data shape (1D = Compressed, 3D = Raw)
            if len(frames.shape) == 1:
                sample = cv2.imdecode(np.frombuffer(frames[0], np.uint8), cv2.IMREAD_UNCHANGED)
                if sample is None: continue
                h, w = sample.shape[:2]
            elif len(frames.shape) >= 3:
                h, w = frames.shape[1:3]
            else:
                continue

            output_path = os.path.join(final_dir, f'{episode_name}_{stream_name}.mp4')
            out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

            # Inner progress bar for individual camera streams
            for frame in tqdm(frames, desc=f"  ↳ {stream_name}", leave=False, colour="cyan"):
                if is_depth:
                    # Handle Depth: normalize numeric values to 8-bit for visualization
                    img_raw = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_UNCHANGED) if len(frames.shape) == 1 else frame
                    depth_float = np.array(img_raw, dtype=np.float32)
                    norm = cv2.normalize(depth_float, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                    img = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
                else:
                    # IMPORTANT NOTE: Since images were compressed in RGB order when saved to HDF5, 
                    # cv2.imdecode returns RGB. We swap to BGR here for OpenCV VideoWriter.
                    img = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        img = img[:, :, [2, 1, 0]]
                
                if img is not None:
                    # Maintain resolution consistency
                    if img.shape[0] != h or img.shape[1] != w:
                        img = cv2.resize(img, (w, h))
                    out.write(img)
            
            # Flush video to disk immediately
            out.release()
        except Exception as e:
            console.print(f"[bold red]Error processing {stream_name} for {episode_name}:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Professional Robot Dataset Visualization Tool")
    parser.add_argument('-i', '--input_dir', required=True, help='Source directory for HDF5 files')
    parser.add_argument('-o', '--output_dir', required=True, help='Root directory for categorized outputs')
    parser.add_argument('--fps', type=float, default=25.0, help='Frames per second')
    parser.add_argument('--depth', action='store_true', help='Toggle to enable depth visualization')
    args = parser.parse_args()

    # Formal Configuration Header
    console.print(Panel.fit(
        f"[bold white]Input Directory:[/bold white] {args.input_dir}\n"
        f"[bold white]Output Directory:[/bold white] {args.output_dir}\n"
        f"[bold white]Depth Visualization:[/bold white] {'Enabled' if args.depth else 'Disabled'}",
        title="[bold green]Visualization Task Initialized[/bold green]",
        border_style="green"
    ))

    # Identify all HDF5 files for global progress tracking
    all_files = [os.path.join(r, f) for r, _, fs in os.walk(args.input_dir) for f in fs if f.endswith('.hdf5')]

    if not all_files:
        console.print("[bold red]No HDF5 files found in the specified input directory.[/bold red]")
        return

    # Overall progress across the entire dataset
    with tqdm(total=len(all_files), desc="Overall Progress", colour="green", unit="file") as pbar:
        for hdf5_path in all_files:
            # Preserve internal folder structure
            rel_path = os.path.relpath(os.path.dirname(hdf5_path), args.input_dir)
            ep_name = os.path.splitext(os.path.basename(hdf5_path))[0]

            data = load_camera_data(hdf5_path, load_depth=args.depth)
            if data:
                save_videos(data, args.fps, args.output_dir, rel_path, ep_name)
            
            pbar.update(1)

    console.print(f"\n[bold green]Success![/bold green] Results saved to subfolders in: [cyan]{args.output_dir}[/cyan]")

if __name__ == '__main__':
    main()
```

### Running the Script

To use this visualization script, follow these steps:

1. Save the code above as `visualize_dataset.py` in your project directory.

2. Install the required Python libraries:

   ```bash
   pip install h5py numpy opencv-python tqdm rich
   ```

3. Run the script with the appropriate arguments:

   ```bash
   python visualize_dataset.py -i /path/to/your/hdf5/directory -o /path/to/output/directory --depth
   ```

   - `-i, --input_dir`: Path to the directory containing HDF5 files.
   - `-o, --output_dir`: Path to the output directory for generated videos.
   - `--fps`: Frames per second for the output videos (default: 25.0).
   - `--depth`: Enable depth visualization (optional).


## **📜 Citation**

If you find our dataset or paper useful, please cite:
```Code snippet
@inproceedings{zeng2026diagnose,
  title={Diagnose, correct, and learn from manipulation failures via visual symbols},
  author={Zeng, Xianchao and Zhou, Xinyu and Li, Youcheng and Shi, Jiayou and Li, Tianle and Chen, Liangming and Ren, Lei and Li, Yong-Lu},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages={42386--42395},
  year={2026}
}
```