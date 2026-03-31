# PrismAudio - Pinokio Installer

> ⚠️ **Early Access — Do Not Install Yet**
> This installer is under active development and still has bugs being worked out. Please wait for a stable release before installing. Star/watch this repo to get notified when it's ready.

🎵 **One-click installer** for [PrismAudio](https://github.com/FunAudioLLM/ThinkSound/tree/prismaudio) — the first Video-to-Audio generation framework with Reinforcement Learning and Chain-of-Thought reasoning. **ICLR 2026 Main Conference**.

![PrismAudio](icon.png)

## Install

1. Install [Pinokio](https://pinokio.computer) if you haven't already
2. Click the button below or paste the URL into Pinokio's address bar:

[![Install on Pinokio](https://img.shields.io/badge/Install%20on-Pinokio-blue?style=for-the-badge)](https://pinokio.computer/item?uri=https://github.com/hoodtronik/PrismAudio.git)

```
https://github.com/hoodtronik/PrismAudio.git
```

3. The installer will ask for your **HuggingFace token** (free account required):
   - [Request access](https://huggingface.co/google/t5gemma-l-l-ul2-it) to the gated T5Gemma model
   - [Create a token](https://huggingface.co/settings/tokens) and paste it when prompted
4. Click **Install** and wait for setup to complete
5. Click **Start** to launch the Gradio web UI

## What It Does

Upload a video and provide an optional text prompt — PrismAudio generates realistic, synchronized audio and merges it back into your video. It uses four specialized CoT modules (Semantic, Temporal, Aesthetic, and Spatial) for multi-dimensional reasoning.

### Features
- **V2A State-of-the-Art** — Best results across all four perceptual dimensions
- **Decomposed CoT Reasoning** — Four specialized reasoning modules
- **Built-in Gradio Web UI** — Upload videos, enter prompts, download results
- **Automatic model download** — Weights are fetched from HuggingFace on first run

### Known Limitations
> [!WARNING]
> **Digital Fuzz / Background Noise:** The current Prismaudio checkpoint is highly usable but natively produces a layer of digital "fuzz" or static over the generated audio. This is an inherent acoustic artifact caused by how the base non-autoregressive DiT (Diffusion Transformer) model decodes the latent space via its VAE.
> 
> *Our installer includes patches that force `bfloat16` precision to prevent catastrophic `float16` static blow-ups on modern GPUs, but the underlying baseline noise floor of the checkpoint itself remains. Future model updates or AI noise-reduction post-processing plugins may be required for pristine production audio.*

## Requirements

- **HuggingFace Account**: Free — needed for the gated [T5Gemma](https://huggingface.co/google/t5gemma-l-l-ul2-it) model
- **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- **Disk**: ~10GB for model weights and dependencies
- **OS**: Windows (tested), Linux (should work)

## API Documentation

### Python
```python
from gradio_client import Client

client = Client("http://localhost:7860")
result = client.predict(
    video_file="path/to/video.mp4",
    caption="A dog barking in the park with wind blowing",
    fn_index=0
)
print(result)  # (status_log, output_video_path)
```

### JavaScript
```javascript
import { Client } from "@gradio/client";

const client = await Client.connect("http://localhost:7860");
const result = await client.predict("/generate_audio", {
    video_file: { path: "path/to/video.mp4" },
    caption: "A dog barking in the park with wind blowing",
});
console.log(result.data);
```

### cURL
```bash
curl -X POST http://localhost:7860/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": ["path/to/uploaded/video.mp4", "A dog barking in the park"],
    "fn_index": 0
  }'
```

## Credits

- [FunAudioLLM/ThinkSound](https://github.com/FunAudioLLM/ThinkSound) — Original PrismAudio repository
- [PrismAudio Paper](https://arxiv.org/abs/2511.18833) — arXiv preprint
- [Pinokio](https://pinokio.computer) — 1-click AI launcher platform
