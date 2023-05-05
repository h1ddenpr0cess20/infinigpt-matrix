import openai
import asyncio
import infinibot

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
infinibot = infinibot.MatrixGPT(server, username, password, channels, personality)

# run main function loop
asyncio.get_event_loop().run_until_complete(infinibot.main())