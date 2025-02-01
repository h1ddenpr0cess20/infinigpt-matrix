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
        options (dict): Additional parameters for the API requests(not implemented at the moment).
        history_size (int): Maximum number of messages per user to retain for context.
        openai_key (str): OpenAI API key.
        xai_key (str): xAI API key.
        google_key (str): Google API key.
        messages (dict): History of conversations per channel and user.
    """
    def __init__(self):
        """Initialize InfiniGPT by loading configuration and setting up attributes."""
        self.config_file = "config.json"
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        self.server, self.username, self.password, self.channels, self.admin = config['matrix'].values()
        self.client = AsyncClient(self.server, self.username)

        self.models, self.api_keys, self.default_model, self.default_personality, self.prompt, self.options, self.history_size = config["llm"].values()
        self.openai_key, self.xai_key, self.google_key = self.api_keys.values()
        self.messages = {}
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger(__name__).info

    async def change_model(self, channel=None, model=None):
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
                "formatted_body": markdown.markdown(message, extensions=['fenced_code', 'nl2br'])},
        )

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

    async def respond(self, sender, messages, sender2=None):
        """
        Generate and send a response using the OpenAI API.

        Args:
            sender (str): User ID of the message sender.
            messages (list): Message history.
            sender2 (str, optional): Additional user ID if .x used.

        Returns:
            tuple: Name to respond to and the AI response
        """
        display_name = await self.display_name(sender)
        if self.model in self.models["openai"]:
            bearer = self.openai_key
            self.url = "https://api.openai.com/v1"
        elif self.model in self.models["xai"]:
            bearer = self.xai_key
            self.url = "https://api.x.ai/v1"
        elif self.model in self.models["google"]:
            bearer = self.google_key
            self.url = "https://generativelanguage.googleapis.com/v1beta/openai"
        elif self.model in self.models["ollama"]:
            bearer = "hello_friend"
            self.url = "http://localhost:11434/v1"

        headers = {
            "Authorization": f"Bearer {bearer}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
        }

        if self.model not in self.models["google"]:
            data.update(self.options)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            url = f"{self.url}/chat/completions"
            response = await client.post(url=url, headers=headers, json=data, timeout=180)
            response.raise_for_status()
            result = response.json()
        name = sender2 if sender2 else sender
        text = result['choices'][0]['message']['content']
        if "<think>" in text:
            thinking, text = text.split("</think>")
            thinking = thinking.strip("<think>").strip()
            self.log(f"Model thinking for {display_name}: {thinking}")
        return name, text.strip()

    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        """
        Set a custom or persona-based prompt for a user.

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
            name, text = await self.respond(sender, self.messages[channel][sender])
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
            if target in self.messages[channel]:
                await self.add_history("user", channel, target, message)
                name, text = await self.respond(target, self.messages[channel][target], sender2=sender)
                await self.add_history("assistant", channel, target, text)
            else:
                pass
        else:
            message = ' '.join(message[1:])
            await self.add_history("user", channel, sender, message)
            name, text = await self.respond(sender, self.messages[channel][sender])
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
