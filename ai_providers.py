import aiohttp
import json
import time
from config import config


class AIProvider:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = ""


class GroqProvider(AIProvider):
    def __init__(self, key):
        super().__init__(key)
        self.base_url = "https://api.groq.com/openai/v1"

    async def chat(self, messages, model, max_tokens=4096, temperature=0.7):
        start = time.time()
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{self.base_url}/chat/completions",
                json={"model": model, "messages": messages,
                      "max_tokens": max_tokens, "temperature": temperature},
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"}) as r:
                d = await r.json()
                el = time.time() - start
                if r.status != 200:
                    return {"error": d.get("error", {}).get("message", f"Error {r.status}"),
                            "response_time": el}
                u = d.get("usage", {})
                return {"response": d["choices"][0]["message"]["content"],
                        "tokens_used": u.get("total_tokens", 0),
                        "tokens_input": u.get("prompt_tokens", 0),
                        "tokens_output": u.get("completion_tokens", 0),
                        "model": d.get("model", model), "response_time": el}


class GeminiProvider(AIProvider):
    def __init__(self, key):
        super().__init__(key)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def _convert(self, msgs):
        sys_parts, conv = [], []
        for m in msgs:
            if m["role"] == "system":
                sys_parts.append(m["content"])
            elif m["role"] == "user":
                conv.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                conv.append({"role": "model", "parts": [{"text": m["content"]}]})
        r = {"contents": conv}
        if sys_parts:
            r["systemInstruction"] = {"parts": [{"text": "\n".join(sys_parts)}]}
        return r

    async def chat(self, messages, model, max_tokens=4096, temperature=0.7):
        start = time.time()
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                json={**self._convert(messages),
                      "generationConfig": {"maxOutputTokens": max_tokens,
                                           "temperature": temperature}}) as r:
                d = await r.json()
                el = time.time() - start
                if r.status != 200:
                    return {"error": d.get("error", {}).get("message", f"Error {r.status}"),
                            "response_time": el}
                try:
                    txt = d["candidates"][0]["content"]["parts"][0]["text"]
                    u = d.get("usageMetadata", {})
                    return {"response": txt,
                            "tokens_used": u.get("totalTokenCount", 0),
                            "tokens_input": u.get("promptTokenCount", 0),
                            "tokens_output": u.get("candidatesTokenCount", 0),
                            "model": model, "response_time": el}
                except Exception as e:
                    return {"error": str(e), "response_time": el}


class OpenRouterProvider(AIProvider):
    def __init__(self, key):
        super().__init__(key)
        self.base_url = "https://openrouter.ai/api/v1"

    async def chat(self, messages, model, max_tokens=4096, temperature=0.7):
        start = time.time()
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{self.base_url}/chat/completions",
                json={"model": model, "messages": messages,
                      "max_tokens": max_tokens, "temperature": temperature},
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"}) as r:
                d = await r.json()
                el = time.time() - start
                if r.status != 200:
                    return {"error": str(d.get("error", {}).get("message", r.status)),
                            "response_time": el}
                u = d.get("usage", {})
                return {"response": d["choices"][0]["message"]["content"],
                        "tokens_used": u.get("total_tokens", 0),
                        "tokens_input": u.get("prompt_tokens", 0),
                        "tokens_output": u.get("completion_tokens", 0),
                        "model": model, "response_time": el}


class CerebrasProvider(AIProvider):
    def __init__(self, key):
        super().__init__(key)
        self.base_url = "https://api.cerebras.ai/v1"

    async def chat(self, messages, model, max_tokens=4096, temperature=0.7):
        start = time.time()
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{self.base_url}/chat/completions",
                json={"model": model, "messages": messages,
                      "max_tokens": max_tokens, "temperature": temperature},
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"}) as r:
                d = await r.json()
                el = time.time() - start
                if r.status != 200:
                    return {"error": str(d.get("error", {}).get("message", r.status)),
                            "response_time": el}
                u = d.get("usage", {})
                return {"response": d["choices"][0]["message"]["content"],
                        "tokens_used": u.get("total_tokens", 0),
                        "tokens_input": u.get("prompt_tokens", 0),
                        "tokens_output": u.get("completion_tokens", 0),
                        "model": model, "response_time": el}


class AIManager:
    def __init__(self):
        self.providers = {}
        self._init()

    def _init(self):
        if config.GROQ_API_KEY:
            self.providers["groq"] = GroqProvider(config.GROQ_API_KEY)
        if config.GEMINI_API_KEY:
            self.providers["gemini"] = GeminiProvider(config.GEMINI_API_KEY)
        if config.OPENROUTER_API_KEY:
            self.providers["openrouter"] = OpenRouterProvider(config.OPENROUTER_API_KEY)
        if config.CEREBRAS_API_KEY:
            self.providers["cerebras"] = CerebrasProvider(config.CEREBRAS_API_KEY)

    def available(self):
        return list(self.providers.keys())

    def models(self, p):
        return config.MODELS.get(p, {})

    def resolve(self, p, mk):
        return config.MODELS.get(p, {}).get(mk, mk)

    async def chat(self, provider_name, messages, model_key, **kw):
        p = self.providers.get(provider_name)
        if not p:
            return {"error": f"Provider '{provider_name}' tidak ada"}
        return await p.chat(messages, self.resolve(provider_name, model_key), **kw)


ai_manager = AIManager()
