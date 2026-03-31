module.exports = {
  run: [
    // Step 0: Prompt for HuggingFace token (needed for gated model google/t5gemma-l-l-ul2-it)
    {
      method: "input",
      params: {
        title: "🔑 HuggingFace Token Required",
        description: [
          "PrismAudio uses Google's T5Gemma model, which requires a free HuggingFace account.",
          "",
          "📋 Follow these steps:",
          "",
          "Step 1️⃣  Create a free account at https://huggingface.co/join",
          "",
          "Step 2️⃣  Go to the model page and click 'Agree and access repository':",
          "   → https://huggingface.co/google/t5gemma-l-l-ul2-it",
          "",
          "Step 3️⃣  Create an access token:",
          "   → https://huggingface.co/settings/tokens",
          "   → Click 'Create new token' → Select 'Read' permission → Copy it",
          "",
          "Step 4️⃣  Paste your token below and click Submit",
        ].join("\n"),
        form: [{
          key: "hf_token",
          title: "HuggingFace Access Token",
          description: "Paste your token here (starts with hf_)",
          type: "password",
          required: true
        }]
      }
    },
    // Step 1: Clone the ThinkSound repo (prismaudio branch) into app/
    {
      when: "{{!exists('app/app.py')}}",
      method: "shell.run",
      params: {
        message: [
          "git clone -b prismaudio https://github.com/FunAudioLLM/ThinkSound.git app",
        ]
      }
    },
    // Step 2: Clone videoprism dependency (required by PrismAudio)
    {
      when: "{{!exists('app/videoprism')}}",
      method: "shell.run",
      params: {
        path: "app",
        message: [
          "git clone https://github.com/google-deepmind/videoprism.git",
        ]
      }
    },
    // Step 3: Install videoprism (--no-deps to skip uvloop chain on Windows)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "uv pip install ./videoprism --no-deps",
          "uv pip install numpy absl-py einops einshape huggingface-hub sentencepiece",
          "uv pip install flax --no-deps",
          "uv pip install jax jaxlib msgpack optax rich typing-extensions",
        ]
      }
    },
    // Step 3a: Fix videoprism GCS paths — download sentencepiece model locally
    // and patch gs:// references that don't work on Windows
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python fix_videoprism_gcs.py",
        ]
      }
    },
    // Step 3b: Login to HuggingFace with the provided token
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "huggingface-cli login --token {{args.hf_token}} --add-to-git-credential",
        ]
      }
    },
    // Step 3c: Save token locally so start.js can inject it as HF_TOKEN env var
    {
      method: "fs.write",
      params: {
        path: ".hf_token",
        text: "{{args.hf_token}}"
      }
    },
    // Step 4: Install inference dependencies manually
    // The upstream requirements.txt fails on Windows due to triton, deepspeed, jax[cuda12]
    // So we install only the packages needed for inference
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          // Core ML (torch installed separately via torch.js)
          "uv pip install torchaudio torchvision safetensors",
          // Training/optimization libs needed at import time
          "uv pip install accelerate peft diffusers transformers",
          // Audio processing
          "uv pip install descript-audio-codec soundfile librosa pyloudnorm torch-stoi pystoi pedalboard laion_clap msclap",
          // Video
          "uv pip install av k-diffusion mediapy moviepy",
          // Vision
          "uv pip install timm clip-anytorch open_clip_torch kornia albumentations",
          // Data
          "uv pip install datasets webdataset pandas scipy scikit-learn scikit-image h5py pyarrow",
          // Config & Utils
          "uv pip install omegaconf hydra-core einops einops-exts lightning torchmetrics torchdiffeq torchsde",
          "uv pip install vector-quantize-pytorch alias-free-torch prefigure randomname aeiou argbind gin-config ml_collections jsonmerge flatten-dict",
          // API & Serving
          "uv pip install gradio fastapi uvicorn",
          // General utilities
          "uv pip install tqdm requests pydantic pillow matplotlib click PyYAML ftfy tiktoken regex numba fire psutil seaborn setuptools",
          // Face detection
          "uv pip install facenet_pytorch==2.6.0 --no-deps",
          // Tensorflow CPU for feature extraction
          "uv pip install tensorflow-cpu==2.15.0",
          // Fix ml_dtypes conflict: tensorflow 2.15 pins 0.2.0 but jax needs >=0.4.0
          "uv pip install \"ml_dtypes>=0.4.0\"",
        ]
      }
    },
    // Step 5: Install correct PyTorch for current GPU
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env",
          path: "app",
          xformers: true
        }
      }
    },
    // Step 6: Install ffmpeg 6.x via conda (torio needs FFmpeg 6 shared libs)
    {
      method: "shell.run",
      params: {
        message: [
          "conda install -y -c conda-forge \"ffmpeg>=6,<7\"",
        ]
      }
    },
    // Step 6b: Copy FFmpeg DLLs into torio/lib so libtorio_ffmpeg6.pyd can load them
    // (Windows only — on Linux/macOS the system linker resolves them automatically)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "python ../fix_ffmpeg.py",
        ]
      }
    },
    // Step 7: Patch app.py with quality & UX improvements
    // (seed control, TF32 precision, Steps/CFG sliders, CoT prompt examples)
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "python ../fix_app.py",
        ]
      }
    },
    {
      method: 'input',
      params: {
        title: 'Installation completed',
        description: 'Click "Start" to launch PrismAudio'
      }
    }
  ]
}
