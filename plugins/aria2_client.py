from aria2p import API, Client as Aria2Client
from config import ARIA2_SECRET, ARIA2_HOST, ARIA2_PORT

# Initialize aria2 client
client = Aria2Client(
    host=ARIA2_HOST,
    port=ARIA2_PORT,
    secret=ARIA2_SECRET
)

# Create API instance
aria2 = API(client)