# Commands

Users can interact with InfiniGPT using dot‑commands or by mentioning the bot name followed by a colon.

## User Commands

- `.ai <message>` or `BotName: <message>` — Chat with the AI (calls tools automatically when enabled).
- `.x <display_name|@user:server> <message>` — Continue another user’s conversation.
- `.persona <text>` — Set or change your personality for the system prompt.
- `.custom <prompt>` — Replace the system prompt with a custom one.
- `.mymodel [name]` — Show or set your personal model (per room/user). Ollama and LM Studio models require matching the global model.
- `.reset` — Clear your history and reset to the default personality.
- `.stock` — Clear your history and run without a system prompt.
- `.help` — Show help text (admin section shown only to admins).

## Admin Commands

- `.model [name|reset]` — Show/change the active model. `reset` restores default.
- `.tools [on|off|toggle|status]` — Toggle tool calling.
- `.clear` — Reset the bot globally for all users.
- `.verbose [on|off|toggle]` — Omit or include the brevity clause for new conversations.
