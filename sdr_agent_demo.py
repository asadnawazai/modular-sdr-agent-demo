import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Dummy lead data (normally comes from Clay, Apollo, or Airtable)
lead = {
    "first_name": "Sarah",
    "last_name": "Anderson",
    "job_title": "Chief Marketing Officer",
    "company": "Brightline Health",
    "industry": "Healthcare",
    "pain_point": "Scaling inbound marketing without increasing team size",
    "email": "sarah@brightline.com"
}

# Prompt template for GPT-4
prompt = f"""
Write a cold outreach email to {lead['job_title']} at {lead['company']}.
They are in the {lead['industry']} industry. 
Their main challenge is: "{lead['pain_point']}".
Use a friendly but professional tone, and keep the message concise.
Sign the email from "Imran
".
"""

# Use API key from environment variable (match the key name in your .env file)
openai.api_key = os.getenv("openai_api_key")

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an SDR assistant helping send great cold emails."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=250
)

# Extract and print the message
email_output = response['choices'][0]['message']['content']
print("=== Personalized Email ===")
print(email_output)