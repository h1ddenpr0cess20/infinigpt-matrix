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

        self.change_model(self.default_model)
        self.personality = self.default_personality
        
        self.join_time = datetime.datetime.now()
        
        self.messages = {}

    def change_model(self, modelname):
        if modelname.startswith("gpt"):
            self.openai.base_url = 'https://api.openai.com/v1'
            self.openai.api_key = self.openai_api_key
        elif modelname.startswith("grok"):
            self.openai.base_url = 'https://api.x.ai/v1/'
            self.openai.api_key = self.xai_api_key
        else:
            self.openai.base_url = 'http://localhost:11434/v1'

        self.model = self.models[self.models.index(modelname)]

    # get the display name for a user
    async def display_name(self, user):
        try:
            name = await self.client.get_displayname(user)
            return name.displayname
        except Exception as e:
            print(e)

    # simplifies sending messages to the channel            
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

    # add messages to the history dictionary
    async def add_history(self, role, channel, sender, message):
        if channel not in self.messages:
            self.messages[channel] = {}
        if sender not in self.messages[channel]:
            self.messages[channel][sender] = [
                {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}
        ]
        self.messages[channel][sender].append({"role": role, "content": message})

        #trim history
        if len(self.messages[channel][sender]) > 24:
            if self.messages[channel][sender][0]["role"] == "system":
                del self.messages[channel][sender][1:3]
            else:
                del self.messages[channel][sender][0:2]

    # create AI response
    async def respond(self, channel, sender, message, sender2=None):
        try:
            #Generate response with AI model
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
            #Extract response text
            response_text = response.choices[0].message.content
            
            #check for unwanted quotation marks around response and remove them
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')

            #add to history
            await self.add_history("assistant", channel, sender, response_text)
            # .x function was used
            if sender2:
                display_name = await self.display_name(sender2)
            # .ai was used
            else:
                display_name = await self.display_name(sender)
            response_text = f"**{display_name}**:\n{response_text.strip()}"
            #Send response to channel
            try:
                await self.send_message(channel, response_text)
            except Exception as e: 
                print(e)

    #set persona or custom system prompt
    async def set_prompt(self, channel, sender, persona=None, custom=None, respond=True):
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        if persona != None and persona != "":
            # combine personality with prompt parts
            prompt = self.prompt[0] + persona + self.prompt[1]
        if custom != None  and custom != "":
            prompt = custom
        await self.add_history("system", channel, sender, prompt)
        if respond:
            await self.add_history("user", channel, sender, "introduce yourself")
            await self.respond(channel, sender, self.messages[channel][sender])

    # tracks the messages in channels
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        # Main bot functionality
        if isinstance(event, RoomMessageText):
            # convert timestamp
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            # assign parts of event to variables
            message = event.body
            sender = event.sender
            sender_display = await self.display_name(sender)
            room_id = room.room_id
            
            #TODO rewrite this section to match ollamarama-matrix updates
            #check if the message was sent after joining and not by the bot
            if message_time > self.join_time and sender != self.username:
                user = await self.display_name(event.sender)
                # main AI response functionality
                if message.startswith(".ai ") or message.startswith(self.bot_id):
                    msg = message.split(" ", 1)
                    msg = msg[1]
                    # check if it violates ToS
                    flagged = await self.moderate(msg)
                    if flagged:
                        await self.send_message(room_id, f"**{sender_display}**: This message violates the OpenAI usage policy and was not sent.")
                        #add a way to penalize repeated violations here, maybe ignore for x amount of time after three violations

                    else:
                        await self.add_history("user", room_id, sender, msg)
                        await self.respond(room_id, sender, self.messages[room_id][sender])

                # collaborative functionality
                if message.startswith(".x "):
                    msg = message.split(" ", 2)
                    msg.pop(0)
                    if len(msg) > 1:
                        disp_name = msg[0]
                        name_id = ""
                        msg = msg[1]
                        if room_id in self.messages:
                            for user in self.messages[room_id]:
                                try:
                                    username = await self.display_name(user)
                                    if disp_name == username:
                                        name_id = user
                                except:
                                    name_id = disp_name
                            flagged = await self.moderate(msg)
                            if flagged:
                                await self.send_message(room_id, f"**{sender_display}**: This message violates the OpenAI usage policy and was not sent.")
                            else:
                                await self.add_history("user", room_id, name_id, msg)
                                await self.respond(room_id, name_id, self.messages[room_id][name_id], sender)

                #change personality    
                if message.startswith(".persona "):
                    msg = message.split(" ", 1)
                    msg = msg[1]
                    flagged = await self.moderate(msg)
                    if flagged:
                            await self.send_message(room_id, f"**{sender_display}**: This persona violates the OpenAI usage policy and was not set.  Choose a new persona.")
                    else:
                        await self.set_prompt(room_id, sender, persona=msg)

                #custom system prompt use   
                if message.startswith(".custom "):
                    msg = message.split(" ", 1)
                    msg = msg[1]
                    flagged = await self.moderate(msg)
                    if flagged:
                            await self.send_message(room_id, f"**{sender_display}**: This custom prompt violates the OpenAI usage policy and was not set.")
                    else:
                        await self.set_prompt(room_id, sender, custom=msg)
                
                #list models
                if message.startswith(".model"):
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        f.close()
                    #load models
                    self.models = config['llm']['models']

                    if message == ".model":
                        await self.send_message(room_id, f"Current model: {self.model}\nAvailable models: " + ", ".join(self.models))
                    #change model if admin
                    if message.startswith(".model ") and sender == self.admin:
                        model = message.split(" ", 1)[1]
                        if model in self.models:
                            self.change_model(model)
                            await self.send_message(room_id, f"Model set to {self.model}")
                        elif model == "reset":
                            self.change_model(self.default_model)
                            await self.send_message(room_id, f"Model set to {self.model}")
                        else:
                            await self.send_message(room_id, "Try again")
                
                # reset bot to default personality
                if message.startswith(".reset"):
                    if room_id in self.messages:
                        if sender in self.messages[room_id]:
                            self.messages[room_id][sender].clear()
                            await self.persona(room_id, sender, self.personality)
                    try:
                        await self.send_message(room_id, f"{self.bot_id} reset to default for {sender_display}")
                    except:
                        await self.send_message(room_id, f"{self.bot_id} reset to default for {sender}")

                # Stock settings, no personality        
                if message.startswith(".stock"):
                    if room_id in self.messages:
                        if sender in self.messages[room_id]:
                            self.messages[room_id][sender].clear()
                    else:
                        self.messages[room_id] = {}
                        self.messages[room_id][sender] = []
                    try:
                        await self.send_message(room_id, f"Stock settings applied for {sender_display}")
                    except:
                        await self.send_message(room_id, f"Stock settings applied for {sender}")
                
                # help menu
                if message.startswith(".help"):
                    with open("help.txt", "r") as f:
                        help_text = f.read()
                        f.close()
                    await self.send_message(room_id, help_text)

    # main loop
    async def main(self):
        # Login, print "Logged in as @alice:example.org device id: RANDOMDID"
        print(await self.client.login(self.password))

        # get account display name
        self.bot_id = await self.display_name(self.username)
        
        # join channels
        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"{self.bot_id} joined {channel}")
                
            except:
                print(f"Couldn't join {channel}")
        
        # start listening for messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        await self.client.sync_forever(timeout=30000, full_state=True) 

if __name__ == "__main__":    
    infinigpt = InfiniGPT()
    
    asyncio.get_event_loop().run_until_complete(infinigpt.main())

