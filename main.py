import logging, os, secrets, pymongo

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


model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", tools=[add, subtract, multiply, divide]
)



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