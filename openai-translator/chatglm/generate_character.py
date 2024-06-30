import os, jwt
import requests
import jwt
import time

def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )

api_key = os.environ["API_KEY"]
token = generate_token(api_key, 60)
url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

file_path = 'stone.md'

with open(file_path, 'r', encoding='utf-8') as file:
    story_text = file.read()

print(story_text)


data = {
    "model": "glm-4",
    "messages": [
        {
            "role": "system",
            "content": "你是一个智谱AI的专家，熟悉智谱AI的CharacterGlm，擅长为用户生成 CharacterGlm 能够产生最好效果的内容"
        },
        {
            "role": "user",
            "content": f"基于以下文本生成角色人设：\n\n{story_text}\n\n 请用不多于200字简要描述两个主要角色的的外貌、性格、背景和特征，用于跟 CharacterGlm 进行交互。"
        }
    ],
    "max_tokens": 8192,
    "temperature": 0.8,
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
ans = response.json()
print(ans)
character_str = ans["choices"][0]["message"]["content"]
print(character_str)