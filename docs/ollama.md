# Ollama Setup (Optional)

InfiniGPT can use local models via [Ollama](https://ollama.com/). This page covers installing Ollama, pulling models, and configuring InfiniGPT to use them.

## Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull at least one model (example):

```bash
ollama pull qwen3
```

## Configure InfiniGPT

Update `config.json`:

```json
{
  "llm": {
    "models": {
      "ollama": ["qwen3", "llama3.2"]
    },
    "default_model": "qwen3",
    "ollama_url": "localhost:11434"
  }
}
```

Notes:

- `llm.models.ollama` is a list of model IDs available on your Ollama server.
- `llm.default_model` can be any configured model across providers, including Ollama models.
- Set `--ollama-url` at launch to point to a remote Ollama host if not local.

## Verify

- Start the bot and check logs for the selected model.
- Test with `.ai` prompts; switch models with `.model <name>`.
