from openai import OpenAI
client = OpenAI(api_key='local', base_url='http://localhost:1234/v1')
response = client.chat.completions.create(
    model='qwen/qwen3-coder-30b',
    messages=[{'role': 'user', 'content': 'Hello!'}]
)