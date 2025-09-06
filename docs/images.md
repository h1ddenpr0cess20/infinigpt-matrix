# Images Directory

InfiniGPT saves generated images to a local `./images/` folder. This is used both as a local archive and as the source when the bot uploads images into Matrix rooms.

## What gets saved

- OpenAI Images tool: `./images/openai_image_<YYYYmmddHHMMSS>.png`
- xAI (Grok) Images tool: `./images/grok_image_<YYYYmmddHHMMSS>.png`
- Google Gemini Images tool: `./images/gemini_image_<YYYYmmddHHMMSS>.png`

Notes:
- The directory is created on demand; no extra setup is required.
- The bot will attempt to upload a returned image path to Matrix and still keep the file on disk.
- The `images/` directory is `.gitignore`’d by default.

## Location and permissions

- Path: relative to the working directory (usually the repo root). If you run the bot from elsewhere, ensure `./images` is writable.
- Linux permissions: if running under a dedicated user or inside a container, verify ownership so the process can write to `./images`.

## Disk usage and retention

- Images accumulate over time. There is no automatic cleanup.
- Periodically delete old files to reclaim space, e.g.:
  - `find ./images -type f -mtime +14 -delete` (delete older than 14 days)
- If you need configurable retention, open an issue describing your use case.

## Docker usage

To persist images outside the container, mount the directory.

- In the official image, `/app/images` is a symlink to `/data/images`. Mount `/data/images` to persist files.

- Example (docker compose service snippet):

```yaml
services:
  infinigpt:
    volumes:
      - ./images:/data/images
```

- Example (docker run):

```bash
mkdir -p images
docker run --rm -it \
  -v "$(pwd)/images":/data/images \
  infinigpt-matrix:latest
```

## Troubleshooting

- “Could not find image file …”: ensure the tool created the file under `./images` and that the path reported by the tool matches the location.
- “Failed to upload image”: check the homeserver supports media upload and your account has permission; also verify network connectivity.
