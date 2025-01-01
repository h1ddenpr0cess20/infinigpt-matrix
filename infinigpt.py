"""
infiniGPT: An AI chatbot for the Matrix chat protocol with infinite personalities with support for OpenAI, xAI, and Ollama models

Author: Dustin Whyte
"""

import asyncio
from nio import AsyncClient, MatrixRoom, RoomMessageText
import datetime
from openai import OpenAI
import json
import markdown

class InfiniGPT:
    def __init__(self):
        self.config_file = "config.json"
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            f.close()
        
        self.server, self.username, self.password, self.channels, self.admin = config['matrix'].values()
        self.client = AsyncClient(self.server, self.username)
        self.openai = OpenAI()

        self.models, self.api_keys, self.default_model, self.default_personality, self.prompt, self.options = config['llm'].values()
        self.openai_api_key, self.xai_api_key = self.api_keys.values()

        self.personality = self.default_personality
        
        self.messages = {}
        
    async def change_model(self, channel=False, model=False):
        if model:
            try:
                if model in self.models:
                    if model.startswith("gpt"):
                        self.openai.base_url = 'https://api.openai.com/v1'
                        self.openai.api_key = self.openai_api_key
                    elif model.startswith("grok"):
                        self.openai.base_url = 'https://api.x.ai/v1/'
                        self.openai.api_key = self.xai_api_key
                    else:
                        self.openai.base_url = 'http://localhost:11434/v1'

                    self.model = self.models[self.models.index(model)]
                    if channel:
                        await self.send_message(channel, f"Model set to **{self.model}**")
            except:
                pass
        else:
            if channel:
                current_model = f"**Current model**: {self.model}\n**Available models**: {', '.join(sorted(list(self.models)))}"
                await self.send_message(channel, current_model)

    async def display_name(self, user):
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            print(e)

    async def send_message(self, channel, message):
        await self.client.room_send(
            room_id=channel,
            message_type="m.room.message",
            content={
                "msgtype": "m.text", 
                "body": message,
                "format": "org.matrix.custom.html",
                "formatted_body": markdown.markdown(message, extensions=['fenced_code', 'nl2br'])},
        )

    # run message through moderation endpoint
    async def moderate(self, message):
        flagged = False
        if not flagged and self.model.startswith("gpt"):
            try:
                moderate = self.openai.moderations.create(model="omni-moderation-latest", input=message,) #run through the OpenAI moderation endpoint
                flagged = moderate.results[0].flagged #true or false
            except:
                pass
        return flagged

    async def add_history(self, role, channel, sender, message):
        if channel not in self.messages:
            self.messages[channel] = {}
        if sender not in self.messages[channel]:
            self.messages[channel][sender] = [
                {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}
        ]
        self.messages[channel][sender].append({"role": role, "content": message})

        if len(self.messages[channel][sender]) > 24:
            if self.messages[channel][sender][0]["role"] == "system":
                del self.messages[channel][sender][1:3]
            else:
                del self.messages[channel][sender][0:2]

    async def respond(self, channel, sender, message, sender2=None):
        try:
            response = self.openai.chat.completions.create(
                    model=self.model,
                    temperature=self.options['temperature'],
                    top_p=self.options['top_p'],
                    frequency_penalty=self.options['frequency_penalty'],
                    messages=message)    
        except Exception as e:
            await self.send_message(channel, "Something went wrong")
            print(e)
        else:
            response_text = response.choices[0].message.content            
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            await self.add_history("assistant", channel, sender, response_text)
            # .x function was used
            if sender2:
                display_name = await self.display_name(sender2)
            # .ai was used
            else:
                display_name = await self.display_name(sender)
            response_text = f"**{display_name}**:\n{response_text.strip()}"
            try:
                await self.send_message(channel, response_text)
            except Exception as e: 
                print(e)

    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        if persona != None and persona != "":
            prompt = self.prompt[0] + persona + self.prompt[1]
        if custom != None  and custom != "":
            prompt = custom
        await self.add_history("system", channel, sender, prompt)
        if respond:
            await self.add_history("user", channel, sender, "introduce yourself")
            await self.respond(channel, sender, self.messages[channel][sender])

    async def ai(self, channel, message, sender, sender_display, x=False):
        try:
            if x and message[2]:
                name = message[1]
                message = ' '.join(message[2:])
                if not await self.moderate(message):
                    if channel in self.messages:
                        for user in self.messages[channel]:
                            try:
                                username = await self.display_name(user)
                                if name == username:
                                    name_id = user
                            except:
                                name_id = name
                        await self.add_history("user", channel, name_id, message)
                        await self.respond(channel, name_id, self.messages[channel][name_id], sender)
                    else:
                        await self.send_message(channel, f"**{sender_display}**: This message violates OpenAI terms of service and was not sent.")
            else:
                message = ' '.join(message[1:])
                if not await self.moderate(message):
                    await self.add_history("user", channel, sender, message)
                    await self.respond(channel, sender, self.messages[channel][sender])
                else:
                        await self.send_message(channel, f"**{sender_display}**: This message violates OpenAI terms of service and was not sent.")
        except:
            pass

    async def reset(self, channel, sender, sender_display, stock=False):
        if channel in self.messages:
            try:
                self.messages[channel][sender].clear()
            except:
                self.messages[channel] = {}
                self.messages[channel][sender] = []
        if not stock:
            await self.send_message(channel, f"{self.bot_id} reset to default for {sender_display}")
            await self.set_prompt(channel, sender, persona=self.personality, respond=False)
        else:
            await self.send_message(channel, f"Stock settings applied for {sender_display}")

    async def help_menu(self, channel):
        with open("help.txt", "r") as f:
            help_menu = f.read()
            f.close()
        await self.send_message(channel, help_menu)

    async def handle_message(self, message, sender, sender_display, channel):
        user_commands = {
            ".ai": lambda: self.ai(channel, message, sender, sender_display),
            f"{self.bot_id}:": lambda: self.ai(channel, message, sender, sender_display),
            ".x": lambda: self.ai(channel, message, sender,sender_display, x=True),
            ".persona": lambda: self.set_prompt(channel, sender, persona=' '.join(message[1:])),
            ".custom": lambda: self.set_prompt(channel, sender, custom=' '.join(message[1:])),
            ".reset": lambda: self.reset(channel, sender, sender_display),
            ".stock": lambda: self.reset(channel, sender, sender_display, stock=True),
            ".help": lambda: self.help_menu(channel),
        }
        admin_commands = {
            ".model": lambda: self.change_model(channel, model=message[1] if len(message) > 1 else False)
        }

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
            await action()
        if sender == self.admin and command in admin_commands:
            action = admin_commands[command]
            await action()

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        if isinstance(event, RoomMessageText):
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            message = event.body
            message = message.split(" ")
            sender = event.sender
            sender_display = await self.display_name(sender)
            channel = room.room_id

            if message_time > self.join_time and sender != self.username:
                try:
                    await self.handle_message(message, sender, sender_display, channel)
                except:
                    pass
                
    async def main(self):
        print(await self.client.login(self.password))

        self.bot_id = await self.display_name(self.username)
        
        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"{self.bot_id} joined {channel}")
                
            except:
                print(f"Couldn't join {channel}")

        self.join_time = datetime.datetime.now()        
        await self.change_model(model=self.default_model)

        self.client.add_event_callback(self.message_callback, RoomMessageText)
        await self.client.sync_forever(timeout=30000, full_state=True) 

if __name__ == "__main__":    
    infinigpt = InfiniGPT()
    
    asyncio.get_event_loop().run_until_complete(infinigpt.main())

