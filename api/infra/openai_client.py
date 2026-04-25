# infra/openai_client.py
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(timeout=30.0)
