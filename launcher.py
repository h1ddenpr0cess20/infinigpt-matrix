import asyncio
import infinigpt
import os

#put a key here and uncomment if not already set in environment
#os.environ['OPENAI_API_KEY'] = "api_key"

api_key = os.environ.get("OPENAI_API_KEY")

server = "https://matrix.org" #change if using different homeserver
username = "@USERNAME:SERVER.TLD" 
password = "PASSWORD"

channels = ["#channel1:SERVER.TLD", 
            "#channel2:SERVER.TLD", 
            "#channel3:SERVER.TLD", 
            "!ExAmPleOfApRivAtErOoM:SERVER.TLD", ] #enter the channels you want it to join here

personality = "an AI that can assume any personality, named InfiniGPT" #change to whatever suits your needs

#bot owner
admin = '@adminname:matrix.org'

# create bot instance
infinigpt = infinigpt.InfiniGPT(server, username, password, channels, personality, admin, api_key)

# run main function loop
asyncio.get_event_loop().run_until_complete(infinigpt.main())