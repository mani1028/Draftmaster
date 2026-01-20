import groq

client = groq.Client(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="llama-3.1-70b",  # updated model name
    messages=[{"role": "user", "content": "Hello Groq!"}]
)

print(response.choices[0].message.content)
