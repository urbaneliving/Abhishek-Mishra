# Client review + site walkthrough

- **Source:** customer testimonial + flat walkthrough (5:20, 1272×720)
- **Task:** replace the old Space Interio logo (company's previous name) with the Urbane Living logo, upscale to 1080p HD
- **Output:** `out/urbane-living-client-review-1080p.mp4` (1920×1080, 30 fps, audio -14 LUFS)

## How it was made
1. `scripts/make_mask.py` + mask step: found the static old-logo pixels from the median of 80 frames
2. `scripts/process.py`: inpaints the old logo on every frame, upscales to 1080p (lanczos + light sharpen/colour), overlays `_brand/urbane-living-logo-HD.png`
