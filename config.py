import logging, os

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# telegram
token = os.getenv("BOT_TOKEN")

# mongodb
def db():
    mongodb = os.getenv("MONGODB_URI")
    client = MongoClient(mongodb, server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    db = client['testing']
    collection = db["sessions"]
    
    return collection

#external api
bible_api_key = os.getenv('BIBLE_API_KEY')
openweather_api_key = os.getenv('OPENWEATHER_API_KEY')

#===========================================================================================#

VERSES = [
  'JER.29.11',
  '1CO.4.4-8',
  'PHP.4.13',
  'JHN.3.16',
  'ROM.8.28',
  'ISA.41.10',
  'PSA.46.1',
  'GAL.5.22-23',
  'HEB.11.1',
  '2TI.1.7',
  '1CO.10.13',
  'PRO.22.6',
  'ISA.40.31',
  'JOS.1.9',
  'HEB.12.2',
  'MAT.11.28',
  'ROM.10.9-10',
  'ROM.8.28',
  'PHP.2.3-4',
  'MAT.5.43-44',
]


bible_params = {
    "content-type": "text",
    "include-notes": "false",
    "include-titles": "false",
    "include-chapter-numbers": "false",
    "include-verse-numbers": "true",
    "include-verse-spans": "false",
    "use-org-id": "false"
}