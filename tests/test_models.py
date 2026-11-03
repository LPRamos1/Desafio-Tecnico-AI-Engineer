from google import genai

client = genai.Client(api_key="SUA_API_KEY")

for model in client.models.list():
    print(model.name, model.supported_actions)