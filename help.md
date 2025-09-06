# InfiniGPT Matrix Bot — Help

Use these commands in any room the bot has joined. You can address the bot with dot‑commands or by mentioning the bot name followed by a colon.

## User Commands

| Command | Description | Example |
| --- | --- | --- |
| `.ai <message>` or `BotName: <message>` | Chat with the AI using your own conversation context. | `.ai Hello there!` |
| `.x <display_name or @user:server> <message>` | Continue another user’s conversation using their context. | `.x Alice What did we decide?` |
| `.persona <personality>` | Change the AI personality (character, style, object, idea, etc.). | `.persona helpful librarian` |
| `.custom <prompt>` | Set a custom system prompt (replaces the roleplay prompt). | `.custom You are a coding tutor.` |
| `.mymodel [name]` | Show or set your personal model (per room/user). | `.mymodel gpt-4o-mini` |
| `.reset` | Clear your history and reset to the default personality. | `.reset` |
| `.stock` | Clear your history and run without a system prompt. | `.stock` |
| `.help` | Show this help message. | `.help` |

~~~

## Admin Commands

| Command | Description | Example |
| --- | --- | --- |
| `.model [name or reset]` | No args: show current and available models. With `name`: change model. Use `reset` to restore default. | `.model qwen3` |
| `.tools [on|off|toggle|status]` | Toggle tool calling on or off. | `.tools toggle` |
| `.clear` | Reset the bot for everyone in the room(s). | `.clear` |
| `.verbose [on|off|toggle]` | Control inclusion of the brevity clause for new conversations. | `.verbose on` |
