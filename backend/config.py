import sqlalchemy
import os, logging
from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pwdlib import PasswordHash
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


# Load the environment variables
load_dotenv()

# Configure the logger
logging.basicConfig(
    filename="ai.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Database URL in format: postgres://user:password@localhost/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a SQLAlchemy engine and sessionmaker
engine = sqlalchemy.create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Configurations for LLAMA and GPT
api_key= os.getenv("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_KEY")
GROQ = os.getenv("LLAMA_MODEL")
GPT = os.getenv("GPT_MODEL")
NANO = os.getenv("GPT_NANO")
JEV = os.getenv("OPENROUTER_API_KEY")


# Method for session creation used with dependency injection
def get_db():
    db = Session()
    try:
        yield db
        db.commit()        # Only runs if NO exception
    except Exception:
        db.rollback()      # Runs for DB errors AND Python errors
        raise              # VERY IMPORTANT
    finally:
        db.close()

# Create LLM instances
llm = ChatGroq(
    model=GROQ, 
    api_key = groq_key,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

llm2 = ChatOpenAI(
    model= GPT,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key= api_key,
)

llm_nano = ChatOpenAI(
    model= NANO,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key= api_key,
)

# Authentication configuration
password_hash = PasswordHash.recommended()

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return username



