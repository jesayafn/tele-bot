import logging, os, secrets, pymongo, requests, random, re

from datetime import datetime

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import google.generativeai as genai


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
mongodb = os.getenv("MONGODB_URI")
clientMongo = MongoClient(mongodb, server_api=ServerApi('1'))
db = clientMongo['testing']
collection = db['sessions']

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


#===========================================================================================#

#===========================================================================================#
class ArrayWithPartsAndRoles:
    def __init__(self):
        self.parts = []
        self.roles = []

    def append(self, parts , role):
        self.parts.append(parts)
        self.roles.append(role)

    def get_part_and_role(self, index):
        if 0 <= index < len(self.parts):
            return self.parts[index], self.roles[index]
        else:
            raise IndexError("Index out of range")

    def __len__(self):
        return len(self.parts)

    def __str__(self):
        parts_roles = [(self.parts[i], self.roles[i]) for i in range(len(self.parts))]
        return str(parts_roles)


def parse_bible_references(reference):
    match = re.match(r'([A-Z0-9]+)\.(\d+)\.(\d+)-(\d+)', reference)
    if match:
        book, chapter, start_verse, end_verse = match.groups()
        start_verse = int(start_verse)
        end_verse = int(end_verse)
        return [f"{book}.{chapter}.{verse}" for verse in range(start_verse, end_verse + 1)]
    else:
        return [reference]
    
def increment_bible_reference(verse_reference):
    # Regular expression to match the verse reference pattern like 'Isa 40:10'
    pattern = r'([a-zA-Z]+) (\d+):(\d+)(?:-(\d+))?'
    match = re.match(pattern, verse_reference)
    
    if match:
        book = match.group(1)
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse
        
        # Increment the end verse by 1
        end_verse += 1
        
        if start_verse == end_verse:
            return f"{book} {chapter}:{start_verse}"
        else:
            return f"{book} {chapter}:{start_verse}-{end_verse}"
    else:
        return "Invalid verse reference format"

#===========================================================================================#

def add(a: float, b: float):
    """returns a + b."""
    return a + b


def subtract(a: float, b: float):
    """returns a - b."""
    return a - b


def multiply(a: float, b: float):
    """returns a * b."""
    return a * b


def divide(a: float, b: float):
    """returns a / b."""
    return a / b

def joke():
    """Fetches a dad joke from the API and returns it."""
    headers = {'Accept': 'text/plain',}
    url = f"https://icanhazdadjoke.com/"
    api_response = requests.get(url,headers=headers)
    return api_response.text


def bible_verse():
    """Fetches a random and selected verse from the bible API and returns it."""
    selected_verses = random.choice(VERSES)
    array_selected_verse = parse_bible_references(selected_verses)
    
    headers = {
        'Accept': 'application/json',
        'api-key': bible_api_key,
        }
    
    reference = ""
    combined_text = ""

    for i, verse in enumerate(array_selected_verse):
        api_url = "https://api.scripture.api.bible/v1/bibles/de4e12af7f28f599-02/verses/" + verse
        response = requests.get(api_url, params=bible_params, headers=headers)
        if response.status_code == 200:
            data = response.json()['data']
            if i == 0:
                book, chapter, first_verse = re.match(r'([A-Z]+)\.(\d+)\.(\d+)', verse).groups()
                reference = f"{book.capitalize()} {chapter}:{first_verse}"
    
                combined_text += data['content'].strip()
            else:
                reference = increment_bible_reference(reference)
                combined_text += f"[{data['verseCount']}] {data['content'].strip()}"
        else:
            return None
    # Removing unnecessary verse count indicators like [1] but keeping verse numbers like [11]
    combined_text = re.sub(r'\[(\d+)\]', lambda m: m.group(1) if int(m.group(1)) > 1 else '', combined_text).strip()

    bible_version = "KJV"
    # print(f"{reference} {combined_text} {bible_version}")
    return reference, combined_text, bible_version















    # for verse in array_selected_verses:
    #     api_url =  "https://api.scripture.api.bible/v1/bibles/de4e12af7f28f599-02/verses/" + verse
    #     response = requests.get(api_url, params=bible_params, headers=headers)
    #     print(api_url)
    #     if response.status_code == 200:
    #         data = response.json()['data']
    #         if not reference:
    #             book, chapter, verse_num = re.match(r'([A-Z]+)\.(\d+)\.(\d+)', verse).groups()
    #             reference = f"{book.capitalize()} {chapter}:{verse_num}"
    #         text = data['content'].strip()
    #         combined_text += text + " "
    #     else:
    #         return None
    
    # combined_text = combined_text.strip()
    # bible_version = "KJV"
    # print(reference, combined_text, bible_version)
    # return reference, combined_text, bible_version
    # api_url =  "https://api.scripture.api.bible/v1/bibles/de4e12af7f28f599-02/verses/"+selected_verse
    # response = requests.get(api_url,params=bible_params,headers=headers)
    # if response.status_code == 200:
    #     data = response.json()['data']
    #     reference = data['reference']
    #     text = data['content'].strip()
    #     bible_version = "KJV"
    #     print(reference, text, bible_version)
    # else:
    #     return None

def city_coordinates(city: str):
    """Fetch city coordinates for get weather information or just get coordinate of city."""
    params = {
        "q"   : city,
        "limit": 1,
        "appid": openweather_api_key,
    }
    
    api_url = "http://api.openweathermap.org/geo/1.0/direct"
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data =  response.json()
        latitude = data[0]["lat"]
        longitude = data[0]["lon"]
        return latitude, longitude
    else:
        return None
    
def city_weather(lat: float, lon: float):
    """Fetch weather information based on coordinates. 
    Units will be used is metric, celcius for temperature and meter per second for speed.
    Milimeter will be used for rain and snow measurements."""
    api_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "appid": openweather_api_key,
    }
    response = requests.get(api_url, params=params)
    
    if response.status_code == 200:
        data =  response.json()
        weather = data["weather"][0]["main"]
        temperature = {
            "current": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
        }
        wind_speed = data["wind"]["speed"]
        return weather, temperature, wind_speed

    else:
        return None

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro", tools=[add, subtract, multiply, divide, joke, bible_verse, city_coordinates,city_weather]
)



#===========================================================================================#    
def get_chat_history(session_id: str) -> list[dict]:
  """Retrieves the chat history for a given session ID."""

  query = {'session_id': session_id}
  document = collection.find_one(query)

  if document:
    chat_history = document.get('chat_history', [])
    return chat_history
  else:
    return [] 




async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # session_status = check_session(user_id)
    # if session_status == 0 or session_status == 2:
    #     await update.message.reply_html(
    #         rf"LMAO, I can't forget you",
    #     )
    # if session_status == 1: 
    session_id = get_session(user_id)
    reset_session(user_id, session_id)
    generate_and_store_session_id(user_id)
    await update.message.reply_html(
        rf"Your session has been reset. ",
    )
    


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I'm a bot powered by LangChain. How can I assist you today?",
        reply_markup=ForceReply(selective=True),
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.effective_user.id
    session_id = None
    session_status = check_session(user_id)

    chat_history = None
    if session_status == 0 or session_status == 2:
        session_id = generate_and_store_session_id(user_id)
        add_session_id(session_id, user_id, False)
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        model_response = chat.send_message(user_message)
        
        chat_history = ArrayWithPartsAndRoles()

        chat_history.append(parts = user_message, role = "user")
        chat_history.append(parts = model_response.text, role="model")
    
    
    
    
    
    
    elif session_status == 1:
        session_id = get_session(user_id)
        chat_history = get_chat_history(session_id)
        chat = model.start_chat(history= chat_history,enable_automatic_function_calling=True)
        model_response = chat.send_message(user_message)
        chat_history = ArrayWithPartsAndRoles()

        chat_history.append(parts = user_message, role = "user")
        chat_history.append(parts = model_response.text, role="model")
        
    
    chat_history_serializable = [{'parts': part, 'role': role} for part, role in zip(chat_history.parts, chat_history.roles)]
    collection.update_one({'session_id': session_id}, {'$push': {'chat_history': {'$each': chat_history_serializable}}}, upsert=True)

        

    await update.message.reply_text(model_response.text)

def generate_and_store_session_id(telegram_user_id: int) -> str:
    # Generate session ID
    session_id = str(telegram_user_id) + secrets.token_urlsafe(32)
    
    # Store in MongoDB
    session_data = {
        'user_id': telegram_user_id,
        'session_id': session_id,
        'reset': False  # Assuming session starts as active
    }
    result = collection.insert_one(session_data)
    
    if result.inserted_id:
        return session_id
    else:
        return None  # Insertion failed

def add_session_id(session_id: str, user_id: int, reset: bool):
    document = {
        'session_id': session_id,
        'user_id': user_id,
        'reset': reset
    }
    
    collection.insert_one(document)

def reset_session(user_id: int, session: str) -> bool:
    query = {'user_id': user_id, 'session_id': session}
    update = {'$set': {'reset': True}}
    
    result = collection.update_one(query, update)
    
    if result.modified_count > 0:
        return True  # Successfully updated at least one document
    else:
        return False  # No document was updated
   
def check_session(user_id: int) -> int:
    query = {'user_id': user_id}
    existing_document = collection.find_one(query, sort=[('_id', pymongo.DESCENDING)])
    
    if existing_document:
        # Document exists
        if existing_document.get('reset', False):
            # reset is true
            return 2
        else:
            # reset is false
            return 1
    else:
        # No document found
        return 0


def get_session(user_id: int) -> str :
    query = {'user_id': user_id, 'reset': False}
    existing_document = collection.find_one(query, sort=[('_id', pymongo.DESCENDING)])
    
    return existing_document.get('session_id', '')
    


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["reset", "stop"], reset))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()