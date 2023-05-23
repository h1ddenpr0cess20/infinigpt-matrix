import openai
import asyncio
import infinigpt

openai.api_key = "API_KEY"

server = "https://matrix.org" #change if using different homeserver
username = "@USERNAME:SERVER.TLD" 
password = "PASSWORD"

channels = ["#channel1:SERVER.TLD", 
            "#channel2:SERVER.TLD", 
            "#channel3:SERVER.TLD", 
            "!ExAmPleOfApRivAtErOoM:SERVER.TLD", ] #enter the channels you want it to join here

personality = "an AI that can assume any personality, named InfiniGPT" #change to whatever suits your needs

# create bot instance
infinigpt = infinigpt.MatrixGPT(server, username, password, channels, personality)

# run main function loop
asyncio.get_event_loop().run_until_complete(infinigpt.main())