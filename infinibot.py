"""
Infinibot: An OpenAI chatbot for the Matrix chat protocol with infinite personalities


Author: Dustin Whyte
Date: May 2023
"""

import asyncio
from nio import AsyncClient, MatrixRoom, RoomMessageText
import datetime
import openai

class MatrixGPT:
    def __init__(self, server, username, password, channels, personality):
        self.server = server
        self.username = username
        self.password = password
        self.channels = channels
        self.personality =  personality

        self.client = AsyncClient(server, username)
        
        # time program started and joined channels
        self.join_time = datetime.datetime.now()
        
        # store chat history
        self.messages = {}

        #prompt parts
        self.prompt = ("assume the personality of ", ".  roleplay and always stay in character unless instructed otherwise.  keep your first response short.")
    
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
            content={"msgtype": "m.text", "body": message},
        )

    # run message through moderation endpoint
    async def moderate(self, message):
        flagged = False
        if not flagged:
            moderate = openai.Moderation.create(input=message) 
            flagged = moderate["results"][0]["flagged"] #true or false
        return flagged

    # add messages to the history dictionary
    async def add_history(self, role, channel, sender, message):
        if channel in self.messages:
            if sender in self.messages[channel]: #if this user exists in the history dictionary
                self.messages[channel][sender].append({"role": role, "content": message}) #add the message
            else:
                self.messages[channel][sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]
        else:
            self.messages[channel]= {}
            self.messages[channel][sender] = {}
            if role == "system":
                self.messages[channel][sender] = [{"role": role, "content": message}]
            else: #add personality to the new user entry
                self.messages[channel][sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]

    # create GPT response
    async def respond(self, channel, sender, message, sender2=None):
        try:
            #Generate response with gpt-3.5-turbo model
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message)    
        except Exception as e:
            print(e)
        else:
            #Extract response text and add it to history
            response_text = response['choices'][0]['message']['content']
            await self.add_history("assistant", channel, sender, response_text)
            if sender2: #if the .x function was used
                display_name = await self.display_name(sender2)
            else: #normal .ai response
                display_name = await self.display_name(sender)
            response_text = display_name + ":\n" + response_text.strip()
            #Send response to channel
            try:
                await self.send_message(channel, response_text)
            except Exception as e: 
                print(e)
            #Shrink history list for token size management (also prevents rate limit error)
            if len(self.messages[channel][sender]) > 14:
                del self.messages[channel][sender][1:3]  #delete the first set of question and answers 

    # change the personality of the bot
    async def persona(self, channel, sender, persona):
        try:
            await self.messages[channel][sender].clear()
        except:
            pass
        personality = self.prompt[0] + persona + self.prompt[1]
        await self.add_history("system", channel, sender, personality) #add to the message history

    # tracks the messages in channels
    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
       
        # Main bot functionality
        if isinstance(event, RoomMessageText):
            # assign parts of event to variables
            # convert timestamp
            message_time = event.server_timestamp / 1000
            message_time = datetime.datetime.fromtimestamp(message_time)
            message = event.body
            sender = event.sender
            sender_display = await self.display_name(sender)
            room_id = room.room_id
            user = await self.display_name(event.sender)

            #check if the message was sent after joining and not by the bot
            if message_time > self.join_time and sender != self.username:
                # main AI response functionality
                if message.startswith(".ai ") or message.startswith(self.bot_id):
                    if message.startswith(self.bot_id):
                        message = message.lstrip(self.bot_id + ":")
                    else:
                        message = message.lstrip(".ai")
                    message = message.strip()
                    # check if it violates ToS
                    flagged = await self.moderate(message)
                    if flagged:
                        await self.send_message(room_id, f"{sender_display}: This message violates the OpenAI usage policy and was not sent.")
                    else:
                        await self.add_history("user", room_id, sender, message)
                        await self.respond(room_id, sender, self.messages[room_id][sender])

                # collaborative functionality
                if message.startswith(".x "):
                    message = message.lstrip(".x")
                    message = message.strip()
                    message = message.split(" ", 1)
                    disp_name = message[0]
                    name_id = ""
                    message = message[1]
                    if room_id in self.messages:
                        for user in self.messages[room_id]:
                            try:
                                username = await self.display_name(user)
                                if disp_name == username:
                                    name_id = user
                            except:
                                name_id = disp_name
                        flagged = await self.moderate(message)
                        if flagged:
                            await self.send_message(room_id, f"{sender_display}: This message violates the OpenAI usage policy and was not sent.")
                        else:
                            await self.add_history("user", room_id, name_id, message)
                            await self.respond(room_id, name_id, self.messages[room_id][name_id], sender)


                #change personality    
                if message.startswith(".persona "):
                    message = event.body.lstrip(".persona")
                    message = message.strip()
                    flagged = await self.moderate(message)
                    if flagged:
                            await self.send_message(room_id, f"{sender_display}: This persona violates the OpenAI usage policy and was not set.  Choose a new persona.")
                    else:
                        await self.persona(room_id, sender, message)
                        await self.respond(room_id, sender, self.messages[room_id][sender])
                
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
                    await self.send_message(room_id, 
f'''{self.bot_id}, an OpenAI chatbot.

.ai <message> or {self.bot_id}: <message>
    Basic usage.
    Personality is preset by bot operator.
    This bot is {self.personality}.

.x <user> <message>
    This allows you to talk to another user's chat history.
    <user> is the display name of the user whose history you want to use
    
.persona <personality type or character or inanimate object>
    Changes the personality.  It can be a character, personality type, object, idea.
    Don't use a custom prompt here.
    If you want to use a custom prompt, use .stock then use .ai <custom prompt>
            
.reset
    Reset to preset personality
    
.stock
    Remove personality and reset to standard GPT settings

Available at https://github.com/h1ddenpr0cess20/infinibot-matrix    
''')

    # main loop
    async def main(self):
        # Login, print "Logged in as @alice:example.org device id: RANDOMDID"
        print(await self.client.login(self.password))

        # start listening for messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        
        # get account display name
        self.bot_id = await self.display_name(self.username)
        
        # join channels
        for channel in self.channels:
            try:
                await self.client.join(channel)
                print(f"{self.bot_id} joined {channel}")
                
            except:
                print(f"Couldn't join {channel}")
        
                     
        await self.client.sync_forever(timeout=30000)  # milliseconds


if __name__ == "__main__":
    openai.api_key = "API_KEY"
    
    server = "https://matrix.org" #change if using different homeserver
    username = "@USERNAME:SERVER.TLD" 
    password = "PASSWORD"

    channels = ["#channel1:SERVER.TLD", 
                "#channel2:SERVER.TLD", 
                "#channel3:SERVER.TLD", 
                "!ExAmPleOfApRivAtErOoM:SERVER.TLD", ] #enter the channels you want it to join here
    
    personality = "an AI that goes above and beyond, named InfiniBot" #change to whatever suits your needs
    
    # create bot instance
    infinibot = MatrixGPT(server, username, password, channels, personality)
    
    # run main function loop
    asyncio.get_event_loop().run_until_complete(infinibot.main())
