"""
infiniGPT: An AI chatbot for the Matrix chat protocol with infinite personalities with support for OpenAI, xAI, and Ollama models

Author: Dustin Whyte
"""

import asyncio
from nio import AsyncClient, MatrixRoom, RoomMessageText
import datetime
import json
import markdown
import httpx
import logging
import logging.config
import mimetypes
import os

from tools import *

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})

class InfiniGPT:
    """
    An AI chatbot for the Matrix chat protocol for use with the OpenAI API, supporting dynamic personalities, 
    custom prompts, model switching, and cross-user interactions.

    Attributes:
        config_file (str): Path to the configuration file.
        server (str): Matrix server URL.
        username (str): Username for the Matrix account.
        password (str): Password for the Matrix account.
        channels (list): List of channel IDs the bot will join.
        admin (str): Admin user ID.
        client (AsyncClient): Matrix client instance.
        models (dict): Available large language models.
        api_keys (dict): API keys for OpenAI, xAI, and Google.
        default_model (str): Default model to use.
        default_personality (str): Default personality for the chatbot.
        prompt (list): Default system prompt structure.
        options (dict): Additional parameters for the API requests.
        history_size (int): Maximum number of messages per user to retain for context.
        ollama_url (str): URL for the Ollama server, default is localhost.
        openai_key (str): OpenAI API key.
        xai_key (str): xAI API key.
        google_key (str): Google API key.
        mistral_key (str): Mistral API key.
        anthropic_key (str): Anthropic API key.
        messages (dict): History of conversations per channel and user.
        tools (list): List of available tools.
        user_models (dict): {channel: {user: model}}
    """
    def __init__(self):
        """Initialize InfiniGPT by loading configuration and setting up attributes."""
        self.config_file = "config.json"
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        with open("schema.json") as f:
            self.tools = json.load(f)
        self.server, self.username, self.password, self.channels, self.admin = config['matrix'].values()
        self.client = AsyncClient(self.server, self.username)

        self.models, self.api_keys, self.default_model, self.default_personality, self.prompt, self.options, self.history_size, self.ollama_url = config["llm"].values()
        self.openai_key, self.xai_key, self.google_key, self.mistral_key, self.anthropic_key = self.api_keys.values()
        self.messages = {}
        self.user_models = {}  # {channel: {user: model}}
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger(__name__).info

    async def change_model(self, channel=None, model=None):
        """
        Change the active LLM model.

        Args:
            channel (str, optional): Channel to send feedback messages to.
            model (str, optional): Desired model to switch to.
        """
        if model != None:
            for provider, models in self.models.items():
                if model in models:
                    self.model = model
                    self.log(f"Model set to {self.model}")
                    if channel != None:
                        await self.send_message(channel, f"Model set to {self.model}")
        else:
            if channel != None:
                current_model = f"**Current model**: {self.model}\n**Available models**: {', '.join([model for provider, models in self.models.items() for model in models])}"
                await self.send_message(channel, current_model)

    async def display_name(self, user):
        """
        Get the display name of a Matrix user.

        Args:
            user (str): User ID.

        Returns:
            str: Display name or user ID if unavailable.
        """
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            self.log(e)

    async def send_message(self, channel, message):
        """
        Send a markdown formatted message to a Matrix room.

        Args:
            channel (str): Room ID.
            message (str): Message content.
        """
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={
                "msgtype": "m.text", 
                "body": message,
                "format": "org.matrix.custom.html",
                "formatted_body": markdown.markdown(message, extensions=['extra', 'fenced_code', 'nl2br', 'sane_lists', 'tables', 'codehilite', 'wikilinks', 'footnotes'])},
        )

    async def send_image(self, channel, image_url=None, filename=None):
        """
        Send an image to a Matrix room using a local file.

        Args:
            channel (str): Room ID.
            image_url (str): Local file path of the image to send.
            filename (str, optional): Filename for the image.
        """
        if not image_url or not os.path.exists(image_url):
            self.log(f"Error sending image: File path '{image_url}' is invalid or file does not exist.")
            await self.send_message(channel, f"Error: Could not find image file at {image_url}")
            return

        if not filename:
            filename = os.path.basename(image_url)

        mime_type = mimetypes.guess_type(image_url)[0] or "application/octet-stream"
        file_stat = os.stat(image_url)

        try:
            with open(image_url, "rb") as image_file:
                upload_response, _ = await self.client.upload(
                    image_file,
                    content_type=mime_type,
                    filename=filename,
                    filesize=file_stat.st_size
                )

            if not upload_response or not hasattr(upload_response, 'content_uri'):
                self.log(f"Failed to upload image: Invalid response from server. Response: {upload_response}")
                await self.send_message(channel, f"Failed to upload image '{filename}'. Server response was invalid.")
                return

            content_uri = upload_response.content_uri

            content = {
                "body": filename,
                "info": {
                    "mimetype": mime_type,
                    "size": file_stat.st_size
                },
                "msgtype": "m.image",
                "url": content_uri
            }

            await self.client.room_send(
                room_id=channel,
                message_type="m.room.message",
                content=content
            )
            self.log(f"Sent image {filename} to {channel}")

        except Exception as e:
            self.log(f"Error sending image to {channel}: {e}")
            await self.send_message(channel, f"Sorry, an error occurred while trying to send the image: {str(e)}")

    async def add_history(self, role, channel, sender, message, default=True):
        """
        Add a message to the interaction history.

        Args:
            role (str): Role of the message sender (e.g., "user", "assistant").
            channel (str): Room ID.
            sender (str): User ID of the sender.
            message (str): Message content.
            default (bool, optional): Whether to add the default system prompt.
        """
        if channel not in self.messages:
            self.messages[channel] = {}
        if sender not in self.messages[channel]:
            self.messages[channel][sender] = []
            if default:
                self.messages[channel][sender].append({"role": "system", "content": self.prompt[0] + self.default_personality + self.prompt[1]})
        self.messages[channel][sender].append({"role": role, "content": message})

        if len(self.messages[channel][sender]) > self.history_size:
            
            if self.messages[channel][sender][0]["role"] == "system":
                self.messages[channel][sender].pop(1)
            else:
                self.messages[channel][sender].pop(0)

            self.messages[channel][sender] = [m for m in self.messages[channel][sender] if not ((m['role'] == "tool") or ('tool_calls' in m))]
    
    async def set_user_model(self, channel, sender, model=None):
        """
        Set or show the LLM model for a specific user in a channel.

        Args:
            channel (str): The Matrix room ID.
            sender (str): The user ID of the person whose model is being set or shown.
            model (str, optional): The name of the model to set for the user. If None, shows the current model and available models.

        """
        display_name = await self.display_name(sender)
        if model is not None:
            ollama_models = self.models.get('ollama', [])
            if model in ollama_models:
                if not (hasattr(self, 'model') and self.model in ollama_models and model == self.model):
                    await self.send_message(channel, "You cannot set an Ollama model unless it matches the current global model. Please ask an admin to change the global model first.")
                    return
            for provider, models in self.models.items():
                if model in models:
                    if channel not in self.user_models:
                        self.user_models[channel] = {}
                    self.user_models[channel][sender] = model
                    self.log(f"Model for {display_name} ({sender}) in {channel} set to {model}")
                    await self.send_message(channel, f"Model for {display_name} set to {model}")
                    return
            await self.send_message(channel, f"Model '{model}' not found. Available: {', '.join([m for ms in self.models.values() for m in ms])}")
        else:
            # Show current model and available models
            user_model = self.user_models.get(channel, {}).get(sender, getattr(self, 'model', self.default_model))
            current_model = f"**Your current model**: {user_model}\n**Available models**: {', '.join([model for provider, models in self.models.items() for model in models])}"
            await self.send_message(channel, current_model)

    async def respond(self, channel, sender, messages, sender2=None):
        """
        Generate a response using the OpenAI API and separate from reasoning if present

        Args:
            sender (str): User ID of the message sender.
            messages (list): Message history.
            sender2 (str, optional): Additional user ID if .x used.

        Returns:
            tuple: Name to respond to and the AI response
        """
        display_name = await self.display_name(sender)
        # Use per-user model if set, else default
        model = self.user_models.get(channel, {}).get(sender, getattr(self, 'model', self.default_model))
        if model in self.models["openai"]:
            bearer = self.openai_key
            url_base = "https://api.openai.com/v1"
        elif model in self.models["xai"]:
            bearer = self.xai_key
            url_base = "https://api.x.ai/v1"
        elif model in self.models["google"]:
            bearer = self.google_key
            url_base = "https://generativelanguage.googleapis.com/v1beta/openai"
        elif model in self.models["mistral"]:
            bearer = self.mistral_key
            url_base = "https://api.mistral.ai/v1"
        elif model in self.models['anthropic']:
            bearer = self.anthropic_key
            url_base = "https://api.anthropic.com/v1"
        elif model in self.models["ollama"]:
            bearer = "hello_friend"
            url_base = f"http://{self.ollama_url}/v1"

        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages,
            "tools": self.tools
        }

        if model not in self.models["google"]:
            data.update(self.options)

        async def get_completion(data):
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=data
                )
                return response.json()

        name = sender2 if sender2 else sender
        url = f"{url_base}/chat/completions"

        result = await get_completion(data)
        max_iterations = 10
        iterations = 0
        while result['choices'][0]['message'].get('tool_calls', []) and iterations < max_iterations:
            msg = result['choices'][0]['message']
            self.messages[channel][sender].append(msg)
            tool_calls = msg.get('tool_calls', [])
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                args = json.loads(tool_call['function']['arguments'])
                self.log(f"Calling tool: {tool_name} with args: {args}")
                try:
                    tool_result = await globals()[tool_name](**args)
                    if isinstance(tool_result, str) and tool_result.lower().endswith(".png"):
                        await self.send_image(channel, image_url=tool_result)
                except Exception as e:
                    self.log(f"Error calling tool {tool_name}: {e}")
                    tool_result = f"Error calling tool {tool_name}: {e}"
                self.messages[channel][sender].append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "content": str(tool_result)
                })
            data["messages"] = self.messages[channel][sender]
            result = await get_completion(data)
            iterations += 1
            
        if iterations >= max_iterations:
            self.log(f"WARNING: Tool calls reached maximum iterations ({max_iterations}) for {sender} in {channel}. Response may be incomplete.")

        iterations = 0
        while result['choices'][0]['message'].get('content') in [None, '', '\n'] and iterations < max_iterations:
            data["messages"] = self.messages[channel][sender]
            result = await get_completion(data)
            iterations += 1
            
        if iterations >= max_iterations:
            self.log(f"WARNING: Empty content handling reached maximum iterations ({max_iterations}) for {sender} in {channel}. Response may be incomplete.")
            
        text = result['choices'][0]['message']['content']

        if "<think>" in text:
            thinking, text = text.split("</think>")
            thinking = thinking.strip("<think>").strip()
            self.log(f"Model thinking for {display_name}: {thinking}")

        return name, text.strip()


    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        """
        Set a custom or persona-based system prompt for a user.

        Args:
            channel (str): Room ID.
            sender (str): User ID of the sender.
            persona (str, optional): Personality name or description.
            custom (str, optional): Custom system prompt.
            respond (bool, optional): Whether to generate a response. Defaults to True.
        """
        display_name = await self.display_name(sender)
        if channel in self.messages:
            if sender in self.messages[channel]:
                self.messages[channel][sender].clear()
        if persona != None:
            system_prompt = self.prompt[0] + persona + self.prompt[1]
        elif custom != None:
            system_prompt = custom
        
        await self.add_history("system", channel, sender, system_prompt, default=False)
        self.log(f"System prompt for {sender} set to '{system_prompt}'")

        if respond:
            await self.add_history("user", channel, sender, "introduce yourself")
            name, text = await self.respond(channel, sender, self.messages[channel][sender])
            await self.add_history("assistant", channel, name, text)
            self.log(f"Sending response to {display_name} in {channel}: {text}")
            await self.send_message(channel, f"**{display_name}**:\n{text}")

    async def ai(self, channel, message, sender, x=False):
        """
        Process AI-related commands and respond accordingly.

        Args:
            channel (str): Room ID.
            message (list): Message content split into parts.
            sender (str): User ID of the sender.
            x (bool): Whether to process cross-user interactions. Defaults to False.
        """
        display_name = await self.display_name(sender)
        self.log(f"{display_name} sent {" ".join(message)} in {channel}")
        if x and message[2]:
            target = message[1]
            message = ' '.join(message[2:])
            if channel in self.messages:
                for user in self.messages[channel]:
                    try:
                        username = await self.display_name(user)
                        if target == username:
                            target = user
                    except:
                        target = name
            if target in self.messages[channel]:
                await self.add_history("user", channel, target, message)
                name, text = await self.respond(channel, target, self.messages[channel][target], sender2=sender)
                await self.add_history("assistant", channel, target, text)
            else:
                pass
        else:
            message = ' '.join(message[1:])
            await self.add_history("user", channel, sender, message)
            name, text = await self.respond(channel, sender, self.messages[channel][sender])
            await self.add_history("assistant", channel, name, text)

        self.log(f"Sending response to {display_name} in {channel}: {text}")
        await self.send_message(channel, f"**{display_name}**:\n{text}")
    

    async def reset(self, channel, sender, stock=False):
        """
        Reset the message history for a specific user in a channel, optionally applying stock settings.

        Args:
            channel (str): Room ID.
            sender (str): User ID whose history is being reset.
            stock (bool): Whether to reset without setting a system prompt.  Defaults to False.
        """
        display_name = await self.display_name(sender)
        if channel not in self.messages:
            self.messages[channel] = {}
        self.messages[channel][sender] = []
        if not stock:
            await self.send_message(channel, f"{self.bot_id} reset to default for {display_name}")
            self.log(f"{self.bot_id} reset to default for {display_name} in {channel}")
            await self.set_prompt(channel, sender, persona=self.default_personality, respond=False)
        else:
            await self.send_message(channel, f"Stock settings applied for {display_name}")
            self.log(f"Stock settings applied for {display_name} in {channel}")

    async def help_menu(self, channel):
        """
        Display the help menu.

        Args:
            channel (str): Room ID.
        """
        with open("help.txt", "r") as f:
            help_menu = f.read()
            f.close()
        await self.send_message(channel, help_menu)

    async def handle_message(self, message, sender, channel):
        """
        Handles messages sent in the channels.
        Parses the message to identify commands or content directed at the bot
        and delegates to the appropriate handler.

        Args:
            message (list): Message content split into parts.
            sender (str): User ID of the sender.
            channel (str): Room ID.
        """
        user_commands = {
            ".ai": lambda: self.ai(channel, message, sender),
            f"{self.bot_id}:": lambda: self.ai(channel, message, sender),
            ".x": lambda: self.ai(channel, message, sender, x=True),
            ".persona": lambda: self.set_prompt(channel, sender, persona=' '.join(message[1:])),
            ".custom": lambda: self.set_prompt(channel, sender, custom=' '.join(message[1:])),
            ".reset": lambda: self.reset(channel, sender),
            ".stock": lambda: self.reset(channel, sender, stock=True),
            ".help": lambda: self.help_menu(channel),
            ".mymodel": lambda: self.set_user_model(channel, sender, message[1] if len(message) > 1 else None),
        }
        admin_commands = {
            ".model": lambda: self.change_model(channel, model=message[1] if len(message) > 1 else None)
        }

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
            await action()
        if sender == self.admin and command in admin_commands:
            action = admin_commands[command]
            await action()

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """
        Handle incoming messages in a Matrix room.

        Args:
            room (MatrixRoom): The room where the message was sent.
            event (RoomMessageText): The event containing the message details.
        """
        if isinstance(event, RoomMessageText):
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            message = event.body.split(" ")
            sender = event.sender
            channel = room.room_id

            if message_time > self.join_time and sender != self.username:
                try:
                    await self.handle_message(message, sender, channel)
                except:
                    pass
                
    async def main(self):
        """
        Initialize the chatbot, log into Matrix, join rooms, and start syncing.

        """
        self.log(await self.client.login(self.password))
        self.bot_id = await self.display_name(self.username)
        
        for channel in self.channels:
            try:
                await self.client.join(channel)
                self.log(f"{self.bot_id} joined {channel}")      
            except:
                self.log(f"Couldn't join {channel}")

        self.join_time = datetime.datetime.now()        
        await self.change_model(model=self.default_model)

        self.client.add_event_callback(self.message_callback, RoomMessageText)
        await self.client.sync_forever(timeout=30000, full_state=True) 

if __name__ == "__main__":    
    infinigpt = InfiniGPT()
    asyncio.run(infinigpt.main())
