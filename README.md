# infinigpt-matrix
InfiniGPT is an OpenAI chatbot for the [Matrix](https://matrix.org/) chat protocol. It has a great prompt which allows it to roleplay as almost anything you can think of. You can set any default personality you would like. It can be changed at any time, and each user has their own separate chat history with their chosen personality setting. Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated, per channel, per user.  

Also available for IRC at [infinigpt-irc](https://github.com/h1ddenpr0cess20/infinigpt-irc/)

## Setup

```
pip3 install matrix-nio openai
```

Get an [OpenAI API](https://platform.openai.com/signup) key 

Set up a [Matrix account](https://app.element.io/) for your bot.  You'll need the server, username and password.

Plug those into the appropriate variables in the launcher.py file.

```
python3 launcher.py
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
    If you want to use a custom prompt, use .stock then use .ai _custom prompt_
        
**.reset**
    Reset to preset personality
    
**.stock**
    Remove personality and reset to standard GPT settings
    
**.help**
    Show the built-in help menu
