# infinigpt-matrix
InfiniGPT is an AI chatbot for the [Matrix](https://matrix.org/) chat protocol, with a great prompt which allows it to roleplay as almost anything you can think of. It supports OpenAI, xAI, Google, Anthropic, Mistral, and Ollama models.  You can set any default personality you would like. It can be changed at any time, and each user has their own separate chat history with their chosen personality setting. Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated, per channel, per user.  

Also available for IRC at [infinigpt-irc](https://github.com/h1ddenpr0cess20/infinigpt-irc/)


## Setup

```
pip install -r requirements.txt
```


Get API keys for each of the LLM providers you would like to use.  Add those to config.json.

Edit the model lists in the config to contain only the models you want to use.  

If you want to use local models, you'll first need to install and familiarize yourself with [Ollama](https://ollama.com/), make sure you can run local LLMs, etc.  If you can't, don't worry about it, you can just omit these models from the config.  

You can install and update it with this command:
```
curl https://ollama.com/install.sh | sh
```

[Download the models](https://ollama.com/search) you want to use and replace the ones I've included as examples in the config.  


Set up a [Matrix account](https://app.element.io/) for your bot.  You'll need the server, username and password.  Add those to the config.json file.
On the first run the script will register a device and save the `device_id` back
into `config.json` so subsequent launches reuse the same device.

Add your own tools under the `infinigpt/tools/` package and extend the schema in `infinigpt/tools/schema.json`.

Current tools included:
- crypto_prices: Fetches price info for a currency pair (e.g., BTC-USD)
- openai_image: Generates images using OpenAI's image API
- grok_image: Generates images using xAI (Grok) image API
- gemini_image: Generates images using Google Gemini image API
- openai_search: Performs a web search using OpenAI's search model

### MCP Tools

InfiniGPT can also load tools exposed via the [Model Context Protocol](https://github.com/modelcontextprotocol).
Define MCP servers under `llm.mcp_servers` in `config.json`. Each server entry
should specify a command or URL. When configured, tools from these servers are
merged with those in `schema.json` and can be invoked like any other tool.

```
infinigpt-matrix --config config.json
```

## Use

**.ai _message_ or botname: _message_**  
    Basic usage.
  
**.x _user message_**  
    This allows you to talk to another user's chat history.  
    _user_ is the display name of the user whose history you want to use
      
**.persona _personality_**  
    Changes the personality.  It can be a character, personality type, object, idea, etc. Don't use a custom system prompt here.

**.custom _prompt_**  
    Allows use of a custom system prompt instead of the built-in one

**.reset**  
    Reset to preset personality
    
**.stock**  
    Remove personality and reset to standard GPT settings

**.model**  
    List available large language models

**.model _modelname_**  
    Change model
    
**.mymodel**  
    List available large language models for yourself and show your current model

**.mymodel _modelname_**  
    Change your model (only affects your own responses)

**.help**
    Show the built-in help menu

## Encryption Support

- This bot supports end-to-end encryption (E2E) in Matrix rooms using `matrix-nio[e2e]` and a built-in device verification system.
- You must have `libolm` installed and available to Python for E2E to work.
- On Windows, you need to build and install `libolm` from source for encryption support. If you do not need encrypted rooms or have issues with `libolm`, use the files in the `no-e2e/` folder.
