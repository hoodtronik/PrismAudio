"""
fix_app.py  –  Post-install patch for app/app.py
=================================================
Applies the following quality & UX improvements to the upstream PrismAudio app.py:

1. PRECISION FLAGS    – Disables TF32 reduced precision (matches upstream generation.py)
2. SEED CONTROL       – Per-inference seed with torch.manual_seed for reproducibility
3. UI CONTROLS        – Adds Steps slider, CFG Scale slider, Seed input to the Gradio UI
4. COT PROMPT GUIDE   – Adds example CoT-style prompts and updated instructions

Run from the project root:  python fix_app.py
"""

import re
import sys
from pathlib import Path

APP_PY = Path(__file__).resolve().parent / "app" / "app.py"

def patch_file():
    if not APP_PY.exists():
        print(f"⚠️  {APP_PY} not found – skipping app.py patches.")
        return

    text = APP_PY.read_text(encoding="utf-8")
    patched = False

    # ================================================================
    # 1. Replace hard-coded seed block with TF32 precision flags
    # ================================================================
    old_seed_block = (
        'seed=42\n'
        'random.seed(seed)\n'
        'np.random.seed(seed)\n'
        'torch.manual_seed(seed)\n'
        'torch.cuda.manual_seed_all(seed)'
    )
    new_precision_block = (
        '# ==================== Precision Flags ====================\n'
        '# Disable TF32 reduced precision for higher quality audio generation\n'
        '# (matches upstream generation.py behavior)\n'
        'torch.backends.cuda.matmul.allow_tf32 = False\n'
        'torch.backends.cudnn.allow_tf32 = False\n'
        'torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False\n'
        'torch.backends.cudnn.benchmark = False'
    )
    # Try with \r\n or \n
    for nl in ['\r\n', '\n']:
        old = old_seed_block.replace('\n', nl)
        if old in text:
            text = text.replace(old, new_precision_block.replace('\n', nl))
            patched = True
            print("✅ Patched: TF32 precision flags")
            break
    else:
        if 'torch.backends.cuda.matmul.allow_tf32 = False' in text:
            print("⏭️  TF32 precision flags already applied")
        else:
            print("⚠️  Could not find seed block to patch for TF32 flags")

    # ================================================================
    # 2. Add seed + steps + cfg_scale params to run_diffusion signature
    # ================================================================
    old_sig = 'def run_diffusion(audio_latent: torch.Tensor, meta: dict, duration: float) -> torch.Tensor:'
    new_sig = ('def run_diffusion(audio_latent: torch.Tensor, meta: dict, duration: float,\n'
               '                  seed: int = -1, steps: int = 24, cfg_scale: float = 5.0) -> torch.Tensor:')
    if old_sig in text:
        text = text.replace(old_sig, new_sig)
        patched = True
        print("✅ Patched: run_diffusion signature (seed/steps/cfg_scale)")
    elif 'seed: int = -1, steps: int = 24' in text:
        print("⏭️  run_diffusion signature already patched")
    else:
        print("⚠️  Could not find run_diffusion signature to patch")

    # ================================================================
    # 3. Add seed control block after latent_length calculation
    # ================================================================
    seed_marker = '    latent_length       = round(SAMPLE_RATE * duration / 2048)\n'
    seed_block = (
        '\n'
        '    # ---- Seed control (matches upstream predict.py / generation.py) ----\n'
        '    if seed == -1:\n'
        '        seed = np.random.randint(0, 2**32 - 1, dtype=np.uint32)\n'
        '    seed = int(seed)\n'
        '    log.info(f"Using seed: {seed}")\n'
        '    torch.manual_seed(seed)\n'
        '    if torch.cuda.is_available():\n'
        '        torch.cuda.manual_seed_all(seed)\n'
    )
    # Try both newline styles
    for nl in ['\r\n', '\n']:
        marker = seed_marker.replace('\n', nl)
        if marker in text and 'Seed control' not in text:
            text = text.replace(marker, marker + seed_block.replace('\n', nl))
            patched = True
            print("✅ Patched: seed control block added")
            break
    else:
        if 'Seed control' in text:
            print("⏭️  Seed control block already present")
        else:
            print("⚠️  Could not find latent_length marker for seed block")

    # ================================================================
    # 4. Replace hard-coded 24 and cfg_scale=5 with parameters
    # ================================================================
    # For v-diffusion
    if 'diffusion.model, noise, 24, 0,' in text:
        text = text.replace('diffusion.model, noise, 24, 0,', 'diffusion.model, noise, steps, 0,')
        patched = True
        print("✅ Patched: v-diffusion uses `steps` param")
    # For rectified flow
    if 'diffusion.model, noise, 24,' in text:
        text = text.replace('diffusion.model, noise, 24,', 'diffusion.model, noise, steps,')
        patched = True
        print("✅ Patched: rectified_flow uses `steps` param")
    if 'cfg_scale=5, batch_cfg=True' in text:
        text = text.replace('cfg_scale=5, batch_cfg=True', 'cfg_scale=cfg_scale, batch_cfg=True')
        patched = True
        print("✅ Patched: cfg_scale parameterized")

    # ================================================================
    # 5. Add comment before noise generation
    # ================================================================
    noise_line = '        noise       = torch.randn([1, diffusion.io_channels, latent_length]).to(DEVICE)'
    comment = '        # Generate noise AFTER setting seed for reproducibility\n'
    if noise_line in text and 'Generate noise AFTER' not in text:
        text = text.replace(noise_line, comment + noise_line)
        patched = True
        print("✅ Patched: noise generation comment")

    # ================================================================
    # 6. Return seed from run_diffusion
    # ================================================================
    old_return = (
        '    return (\n'
        '        fakes.to(torch.float32)\n'
        '             .div(torch.max(torch.abs(fakes)))\n'
        '             .clamp(-1, 1)\n'
        '             .mul(32767)\n'
        '             .to(torch.int16)\n'
        '             .cpu()\n'
        '    )\n'
    )
    new_return = (
        '    return (\n'
        '        fakes.to(torch.float32)\n'
        '             .div(torch.max(torch.abs(fakes)))\n'
        '             .clamp(-1, 1)\n'
        '             .mul(32767)\n'
        '             .to(torch.int16)\n'
        '             .cpu()\n'
        '    ), seed\n'
    )
    for nl in ['\r\n', '\n']:
        old = old_return.replace('\n', nl)
        if old in text:
            text = text.replace(old, new_return.replace('\n', nl))
            patched = True
            print("✅ Patched: run_diffusion returns seed")
            break
    else:
        if '), seed' in text:
            print("⏭️  run_diffusion already returns seed")
        else:
            print("⚠️  Could not patch run_diffusion return")

    # ================================================================
    # 7. Update generate_audio signature
    # ================================================================
    old_gen_sig = 'def generate_audio(video_file, caption: str):'
    new_gen_sig = 'def generate_audio(video_file, caption: str, seed: int = -1, steps: int = 24, cfg_scale: float = 5.0):'
    if old_gen_sig in text:
        text = text.replace(old_gen_sig, new_gen_sig)
        patched = True
        print("✅ Patched: generate_audio signature")
    elif 'seed: int = -1, steps: int = 24' in text:
        print("⏭️  generate_audio signature already patched")

    # ================================================================
    # 8. Update run_diffusion call site in generate_audio
    # ================================================================
    old_call = 'generated_audio = run_diffusion(audio_latent, meta, duration)'
    new_call = ('generated_audio, used_seed = run_diffusion(audio_latent, meta, duration,\n'
                '                                                    seed=seed, steps=int(steps), cfg_scale=float(cfg_scale))')
    if old_call in text:
        text = text.replace(old_call, new_call)
        patched = True
        print("✅ Patched: run_diffusion call site")

    # Add seed/steps/cfg logging after the call
    old_shape_log = '        log_step(f"   Generated audio shape : {tuple(generated_audio.shape)}")'
    new_shape_log = ('        log_step(f"   Generated audio shape : {tuple(generated_audio.shape)}")\n'
                     '        log_step(f"   Seed: {used_seed}  |  Steps: {int(steps)}  |  CFG: {float(cfg_scale)}")')
    if old_shape_log in text and 'used_seed' not in text.split(old_shape_log)[0].split('\n')[-1]:
        # Only add if not already referencing used_seed nearby
        if 'Seed: {used_seed}' not in text:
            text = text.replace(old_shape_log, new_shape_log)
            patched = True
            print("✅ Patched: seed/steps/cfg logging")

    # ================================================================
    # 9. Patch Gradio UI – add seed/steps/cfg controls
    # ================================================================
    # Update prompt placeholder
    old_placeholder = (
        'placeholder=(\n'
        '                        "Describe the audio you want to generate, e.g.:\\n"\n'
        '                        "A dog barking in the park with wind blowing"\n'
        '                    ),'
    )
    new_placeholder = (
        'placeholder=(\n'
        '                        "Describe the audio in detail (Chain-of-Thought style), e.g.:\\n"\n'
        '                        "Generate the sound of a hedge trimmer running steadily, "\n'
        '                        "focusing on consistent motor noise and cutting sounds. "\n'
        '                        "Ensure minimal background noise or voices."\n'
        '                    ),'
    )
    if 'A dog barking in the park' in text:
        text = text.replace(old_placeholder, new_placeholder)
        text = text.replace('label="Caption / Prompt"', 'label="Caption / CoT Prompt"')
        patched = True
        print("✅ Patched: prompt placeholder with CoT guidance")

    # Add seed/steps/cfg controls before the buttons
    old_buttons = (
        '                with gr.Row():\n'
        '                    clear_btn  = gr.Button("🗑️ Clear",         variant="secondary", scale=1)\n'
        '                    submit_btn = gr.Button("🚀 Generate Audio", variant="primary",   scale=2)\n'
    )
    new_controls_and_buttons = (
        '                with gr.Row():\n'
        '                    seed_input = gr.Number(\n'
        '                        label="Seed (-1 = random)",\n'
        '                        value=-1,\n'
        '                        precision=0,\n'
        '                        scale=1,\n'
        '                    )\n'
        '                    steps_slider = gr.Slider(\n'
        '                        minimum=1, maximum=100, step=1, value=24,\n'
        '                        label="Steps",\n'
        '                        info="More steps = better quality but slower (default: 24)",\n'
        '                        scale=1,\n'
        '                    )\n'
        '                    cfg_slider = gr.Slider(\n'
        '                        minimum=1.0, maximum=15.0, step=0.5, value=5.0,\n'
        '                        label="CFG Scale",\n'
        '                        info="Prompt adherence strength (default: 5.0)",\n'
        '                        scale=1,\n'
        '                    )\n'
        '                with gr.Row():\n'
        '                    clear_btn  = gr.Button("🗑️ Clear",         variant="secondary", scale=1)\n'
        '                    submit_btn = gr.Button("🚀 Generate Audio", variant="primary",   scale=2)\n'
    )
    if 'seed_input' not in text:
        for nl in ['\r\n', '\n']:
            old = old_buttons.replace('\n', nl)
            if old in text:
                text = text.replace(old, new_controls_and_buttons.replace('\n', nl))
                patched = True
                print("✅ Patched: Added seed/steps/cfg UI controls")
                break

    # ================================================================
    # 10. Add CoT prompt examples accordion
    # ================================================================
    old_instructions = '        with gr.Accordion("📖 Instructions", open=False):'
    cot_accordion = (
        '        with gr.Accordion("💡 Prompt Examples (CoT-style works best!)", open=False):\n'
        '            gr.Markdown("""\n'
        '**PrismAudio works best with detailed, structured Chain-of-Thought (CoT) descriptions.**\n'
        'Instead of short captions, describe *what sounds*, *how they sound*, and *what to avoid*.\n'
        '\n'
        '| Simple (worse) | CoT-style (better) |\n'
        '|---|---|\n'
        '| "bowling" | "Start with ambient background, then add consistent sounds of bowling balls striking pins. Include occasional subtle sounds of pins rattling and settling. Keep voices minimal." |\n'
        '| "chopping food" | "Generate rhythmic chopping sounds consistent with food being sliced, incorporating occasional rustling noises like a plastic bag. Avoid adding human voices, ensuring a focused kitchen scene." |\n'
        '| "playing tennis" | "Generate sounds of a tennis ball hitting a racket, the ball bouncing, and player grunts, with distant court ambient noise. Avoid unrelated sounds. Focus on clear tennis audio cues." |\n'
        '| "printer" | "Generate continuous printer printing sounds with periodic beeps, including paper movement and occasional beeps for realism. Add subtle ambient background noise for authenticity." |\n'
        '            """)\n'
        '\n'
    )
    if 'CoT-style works best' not in text and old_instructions in text:
        text = text.replace(old_instructions, cot_accordion + '        ' + old_instructions.lstrip())
        patched = True
        print("✅ Patched: Added CoT prompt examples accordion")

    # Update instructions text
    old_inst_content = (
        '1. Upload a video file (mp4 / avi / mov / etc.).\n'
        '2. Enter a text prompt describing the desired audio content.\n'
        '3. Click **🚀 Generate Audio** and watch the log on the right for progress.\n'
        '4. The output video (original visuals + generated audio) appears below when done.'
    )
    new_inst_content = (
        '1. Upload a video file (mp4 / avi / mov / etc.).\n'
        '2. Enter a **detailed CoT-style prompt** describing the desired audio content.\n'
        '3. Set a **seed** for reproducibility (-1 = random). If you get a good result, note the seed from the log!\n'
        '4. Click **🚀 Generate Audio** and watch the log on the right for progress.\n'
        '5. The output video (original visuals + generated audio) appears below when done.'
    )
    if 'Enter a text prompt' in text:
        text = text.replace(old_inst_content, new_inst_content)
        patched = True
        print("✅ Patched: Updated instructions with seed info")

    # ================================================================
    # 11. Update event bindings to include new controls
    # ================================================================
    old_bindings = 'inputs=[video_input, caption_input],'
    new_bindings = 'inputs=[video_input, caption_input, seed_input, steps_slider, cfg_slider],'
    if old_bindings in text:
        text = text.replace(old_bindings, new_bindings)
        patched = True
        print("✅ Patched: Event bindings include seed/steps/cfg")

    # Update clear_all
    old_clear = 'return None, "", "", None'
    new_clear = 'return None, "", -1, 24, 5.0, "", None'
    if old_clear in text:
        text = text.replace(old_clear, new_clear)
        patched = True
        print("✅ Patched: clear_all includes seed/steps/cfg")

    old_clear_outputs = 'outputs=[video_input, caption_input, log_output, video_output],'
    new_clear_outputs = 'outputs=[video_input, caption_input, seed_input, steps_slider, cfg_slider, log_output, video_output],'
    if old_clear_outputs in text:
        text = text.replace(old_clear_outputs, new_clear_outputs)
        patched = True
        print("✅ Patched: clear outputs include seed/steps/cfg")

    # ================================================================
    # 12. Enforce MP4 / YUV420p standard
    # ================================================================
    old_convert = (
        '    result = subprocess.run(\n'
        '        [\n'
        '            "ffmpeg", "-y", "-i", src,\n'
        '            "-c:v", "libx264", "-preset", "fast",\n'
    )
    new_convert = (
        '    result = subprocess.run(\n'
        '        [\n'
        '            "ffmpeg", "-y", "-i", src,\n'
        '            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",\n'
    )
    for nl in ['\r\n', '\n']:
        old = old_convert.replace('\n', nl)
        if old in text:
            text = text.replace(old, new_convert.replace('\n', nl))
            patched = True
            print("✅ Patched: MP4 conversion uses yuv420p format")
            break

    old_skip = (
        '        if src_ext != ".mp4":\n'
        '            log_step("   Converting to mp4...")\n'
        '            ok, err = convert_to_mp4(video_file, mp4_path)\n'
        '            if not ok:\n'
        '                yield log_step(f"❌ Video conversion failed:\\n{err}"), None\n'
        '                return\n'
        '        else:\n'
        '            shutil.copy(video_file, mp4_path)'
    )
    new_skip = (
        '        log_step("   Ensuring video is h264/yuv420p MP4...")\n'
        '        ok, err = convert_to_mp4(video_file, mp4_path)\n'
        '        if not ok:\n'
        '            yield log_step(f"❌ Video conversion failed:\\n{err}"), None\n'
        '            return'
    )
    for nl in ['\r\n', '\n']:
        old = old_skip.replace('\n', nl)
        if old in text:
            text = text.replace(old, new_skip.replace('\n', nl))
            patched = True
            print("✅ Patched: Enforce video conversion for ALL formats")
            break

    # ================================================================
    # 13. Fix audio static caused by float16 autocast
    # ================================================================
    old_autocast_1 = "        with torch.amp.autocast('cuda'):\n            conditioning ="
    new_autocast_1 = (
        "        autocast_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float32\n"
        "        with torch.autocast(device_type='cuda', dtype=autocast_dtype):\n"
        "            conditioning ="
    )
    old_autocast_2 = "        with torch.amp.autocast('cuda'):\n            if diffusion_objective"
    new_autocast_2 = "        with torch.autocast(device_type='cuda', dtype=autocast_dtype):\n            if diffusion_objective"

    for nl in ['\r\n', '\n']:
        old1 = old_autocast_1.replace('\n', nl)
        old2 = old_autocast_2.replace('\n', nl)
        
        if old1 in text and old2 in text:
            text = text.replace(old1, new_autocast_1.replace('\n', nl))
            text = text.replace(old2, new_autocast_2.replace('\n', nl))
            patched = True
            print("✅ Patched: Replaced torch.amp.autocast with bfloat16/float32 safe autocast")
            break

    # ================================================================
    # Write out
    # ================================================================
    if patched:
        APP_PY.write_text(text, encoding="utf-8")
        print(f"\n✅ All patches applied to {APP_PY}")
    else:
        print(f"\n⏭️  No patches needed – {APP_PY} already up to date")


if __name__ == "__main__":
    patch_file()
