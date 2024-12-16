# infinigpt-matrix
InfiniGPT is an OpenAI chatbot for the [Matrix](https://matrix.org/) chat protocol. It has a great prompt which allows it to roleplay as almost anything you can think of. You can set any default personality you would like. It can be changed at any time, and each user has their own separate chat history with their chosen personality setting. Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated, per channel, per user.  

Also available for IRC at [infinigpt-irc](https://github.com/h1ddenpr0cess20/infinigpt-irc/)

Now with Grok and Ollama support, and model switching.

## Setup

```
pip3 install matrix-nio openai 
```


Get an [OpenAI API](https://platform.openai.com/signup) key. Get an [xAI API](https://accounts.x.ai/) key, if you want.  Add those to config.json.

Add desired Ollama models to the models list in config.json, if using.  You'll first need to install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run local LLMs, etc.  If you can't, don't worry about it, you can just omit these models from the config.

You can install and update it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the config.json file.  If you want to use the ones I've included, just run ollama pull _modelname_ for each.

Set up a [Matrix account](https://app.element.io/) for your bot.  You'll need the server, username and password.  Add those to the config.json file.

```
python3 infinigpt.py
```

## Use

**.ai _message_ or botname: _message_**
    Basic usage.
    Personality is preset by bot operator.
  
**.x _user message_**
    This allows you to talk to another user's chat history.
    _user_ is the display name of the user whose history you want to use
      
**.persona _personality_**
    Changes the personality.  It can be a character, personality type, object, idea.
    Don't use a custom prompt here.

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

**.model reset**
    Reset model
    
**.help**
    Show the built-in help menu
