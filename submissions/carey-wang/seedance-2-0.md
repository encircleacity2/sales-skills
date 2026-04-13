---
name: seedance-2-0
description: Unified Seedance 2.0 skill for prompt design and async web submission. Use for text-to-video, image-to-video, reference-driven prompting, Chinese prompt optimization, camera/motion/lighting/style direction, audio/lip-sync guidance, content-filter-safe rewrites, troubleshooting, and submitting async Seedance requests from code.
---

# Seedance 2.0

This skill is the single entry point for Seedance 2.0 in this workspace. Prompt guidance that used to live across multiple `seedance-*` skills is consolidated here and split into on-demand references.

## Use this skill for

- Turning a vague idea into a production-ready Seedance prompt
- Writing or compressing Chinese prompts
- Planning camera, motion, lighting, character, style, VFX, and audio direction
- Rewriting prompts to avoid slop, copyright collisions, and content-filter blocks
- Troubleshooting drift, jitter, broken lip-sync, or weak outputs
- Submitting Seedance generation through the async Python entrypoint

## Loading map

- Read [workflow](references/workflow.md) when the user needs ideation, genre routing, or I2V/T2V decision rules.
- Read [prompt-guidance](references/prompt-guidance.md) when building or compressing the actual prompt text.
- Read [shot-design](references/shot-design.md) for camera, motion, lighting, characters, style, and VFX.
- Read [audio](references/audio.md) for dialogue, music, lip-sync, and beat-sync.
- Read [safety](references/safety.md) for copyright, content filters, anti-slop rewrites, and troubleshooting.
- Read [examples](references/examples.md) for genre templates and Chinese examples.
- Read [vocabulary-zh](references/vocabulary-zh.md) when the user wants prompt-ready Chinese film language.
- Read [platform](references/platform.md) for operational constraints, asset budgets, and downstream pipeline notes.

## Core rules

1. Intent over micromanagement. Tell the model what happens and how it should feel.
2. References beat description. If the user has assets, use them.
3. In I2V, describe motion and camera only. Do not restate the image.
4. One primary camera move per shot.
5. Keep prompts dense. Default target: 30-100 Chinese words or one compact paragraph.
6. Use async submission only. Do not build sync waiting or cron-based monitoring into this skill.
7. If the user wants to submit a Seedance request but has not provided cookies, ask them for the Jimeng cookies first and explain how to obtain them. Do not assume cookies already exist.
8. After the user provides cookies, save them locally before submission so later requests can reuse the same local file.

## Async request API

The only supported code entrypoint is:

```python
from scripts.async_generate_video import async_generate_video
```

Example:

```python
result = async_generate_video(
    cookies=cookies,
    prompt="银色咖啡机置于现代厨房台面。晨光切入，蒸汽缓慢升起，镜头缓推到咖啡液流入玻璃杯的特写。",
    image_urls="https://example.com/product.jpg",
    video_aspect_ratio="9:16",
    video_duration=5,
)
```

The function submits immediately, performs one status lookup, and returns:

```python
{
    "submit_id": "uuid",
    "status": "queued" | "processing" | "success" | "failed",
    "queue_position": 12,
    "estimated_wait_time": 300,
    "message": "Video queued at position 12, estimated wait time: 300 seconds."
}
```

## Inputs

- `cookies`: required Jimeng / Dreamina cookie string
- `prompt`: required prompt text
- `image_urls`: optional string or list of strings; images are auto-uploaded before submission
- `video_aspect_ratio`: optional, default `1:1`
- `video_duration`: optional, default `5`
- `submit_id`: optional custom request id

If `cookies` is missing, stop and ask the user to provide it. Use the retrieval steps from [platform](references/platform.md). After receiving the cookie string, save it to the local cookie file described there and then proceed.