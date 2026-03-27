"""
LLM Provider - 大语言模型接口模块
支持本地模型 (Ollama, LM Studio) 和 OpenAI 兼容 API
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Generator
from enum import Enum
import urllib.request
import urllib.error


class ProviderType(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    GROQ = "groq"
    TOGETHER = "together"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    provider: str = "ollama"
    api_base: str = "http://localhost:11434/v1"
    api_key: str = "not-needed"
    model: str = "llama3"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
    stream: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "api_base": self.api_base,
            "api_key": self.api_key,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "stream": self.stream
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        return cls(**data)

    @classmethod
    def from_env(cls) -> 'LLMConfig':
        provider = os.getenv("LLM_PROVIDER", "ollama")
        api_base = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
        api_key = os.getenv("LLM_API_KEY", "not-needed")
        model = os.getenv("LLM_MODEL", "llama3")

        return cls(
            provider=provider,
            api_base=api_base,
            api_key=api_key,
            model=model
        )


class LLMProvider:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self._client = None

    @classmethod
    def from_config_file(cls, path: str = "./llm_config.json") -> 'LLMProvider':
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                config = LLMConfig.from_dict(data)
        else:
            config = LLMConfig.from_env()
        return cls(config)

    def save_config(self, path: str = "./llm_config.json"):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        if self.config.provider == ProviderType.ANTHROPIC.value:
            return self._chat_anthropic(messages, model, max_tokens, temperature)
        else:
            return self._chat_openai_compatible(messages, model, temperature, max_tokens, stream)

    def _chat_openai_compatible(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> Dict[str, Any]:
        url = f"{self.config.api_base.rstrip('/')}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }

        if self.config.provider not in [ProviderType.OLLAMA.value, ProviderType.LM_STUDIO.value]:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        if self.config.provider == ProviderType.OLLAMA.value:
            payload["options"] = {}
            if temperature != self.config.temperature:
                payload["options"]["temperature"] = temperature
            if max_tokens != self.config.max_tokens:
                payload["options"]["num_predict"] = max_tokens

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return response_data

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise Exception(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise Exception(f"Connection error: {e.reason}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01"
        }

        system_msg = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                filtered_messages.append(msg)

        payload = {
            "model": model,
            "messages": filtered_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if system_msg:
            payload["system"] = system_msg

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
            return json.loads(response.read().decode('utf-8'))

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Generator[str, None, None]:
        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.temperature

        response = self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            stream=True
        )

        if "choices" in response:
            for chunk in response["choices"]:
                if "delta" in chunk and "content" in chunk["delta"]:
                    yield chunk["delta"]["content"]
        elif "content" in response:
            yield response["content"]

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.chat(messages, **kwargs)

        if "choices" in response:
            return response["choices"][0]["message"]["content"]
        elif "content" in response:
            return response["content"]
        else:
            raise Exception(f"Unexpected response format: {response}")

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for content in self.chat_stream(messages, **kwargs):
            yield content

    def is_available(self) -> bool:
        try:
            if self.config.provider == ProviderType.OLLAMA.value:
                url = f"{self.config.api_base.rstrip('/')}/tags"
            else:
                url = f"{self.config.api_base.rstrip('/')}/models"

            req = urllib.request.Request(url, method='GET')
            if self.config.provider not in [ProviderType.OLLAMA.value, ProviderType.LM_STUDIO.value]:
                req.add_header("Authorization", f"Bearer {self.config.api_key}")

            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False

    def list_models(self) -> List[str]:
        try:
            if self.config.provider == ProviderType.OLLAMA.value:
                url = f"{self.config.api_base.rstrip('/')}/tags"
            else:
                url = f"{self.config.api_base.rstrip('/')}/models"

            req = urllib.request.Request(url, method='GET')
            if self.config.provider not in [ProviderType.OLLAMA.value, ProviderType.LM_STUDIO.value]:
                req.add_header("Authorization", f"Bearer {self.config.api_key}")

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                if "models" in data:
                    return [m.get("name", m.get("id", "unknown")) for m in data["models"]]
                elif "data" in data:
                    return [m.get("id", "unknown") for m in data["data"]]
                else:
                    return [self.config.model]

        except Exception as e:
            return [self.config.model]


def create_llm_config() -> LLMConfig:
    print("\n" + "="*50)
    print("LLM 配置向导")
    print("="*50)

    print("\n选择模型提供商:")
    print("  1. Ollama (本地模型)")
    print("  2. LM Studio (本地模型)")
    print("  3. OpenAI API")
    print("  4. Groq")
    print("  5. Together AI")
    print("  6. Anthropic (Claude)")
    print("  7. 自定义 (其他兼容 OpenAI API 的服务)")

    while True:
        choice = input("\n选择 (1-7): ").strip()
        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            break
        print("无效选择")

    provider_map = {
        '1': ProviderType.OLLAMA,
        '2': ProviderType.LM_STUDIO,
        '3': ProviderType.OPENAI,
        '4': ProviderType.GROQ,
        '5': ProviderType.TOGETHER,
        '6': ProviderType.ANTHROPIC,
        '7': ProviderType.CUSTOM
    }
    provider = provider_map[choice].value

    base_urls = {
        ProviderType.OLLAMA.value: "http://localhost:11434/v1",
        ProviderType.LM_STUDIO.value: "http://localhost:1234/v1",
        ProviderType.OPENAI.value: "https://api.openai.com/v1",
        ProviderType.GROQ.value: "https://api.groq.com/openai/v1",
        ProviderType.TOGETHER.value: "https://api.together.ai/v1",
        ProviderType.ANTHROPIC.value: "https://api.anthropic.com/v1",
        ProviderType.CUSTOM.value: "http://localhost:8000/v1"
    }

    api_base = input(f"\nAPI Base URL [{base_urls.get(provider, 'http://localhost:8000/v1')}]: ").strip()
    if not api_base:
        api_base = base_urls.get(provider, "http://localhost:8000/v1")

    api_key = ""
    if provider not in [ProviderType.OLLAMA.value, ProviderType.LM_STUDIO.value]:
        api_key = input("API Key: ").strip()
        if not api_key:
            api_key = "not-needed"

    model_suggestions = {
        ProviderType.OLLAMA.value: "llama3",
        ProviderType.LM_STUDIO.value: "local-model",
        ProviderType.OPENAI.value: "gpt-4",
        ProviderType.GROQ.value: "llama-3.1-70b-versatile",
        ProviderType.TOGETHER.value: "meta-llama/Llama-3-70b-chat-hf",
        ProviderType.ANTHROPIC.value: "claude-3-opus-20240229",
        ProviderType.CUSTOM.value: "custom-model"
    }

    model = input(f"\n模型名称 [{model_suggestions.get(provider, 'gpt-4')}]: ").strip()
    if not model:
        model = model_suggestions.get(provider, "gpt-4")

    temperature = 0.7
    temp_input = input("\nTemperature [0.7]: ").strip()
    if temp_input:
        try:
            temperature = float(temp_input)
        except:
            temperature = 0.7

    max_tokens = 4096
    tokens_input = input("Max Tokens [4096]: ").strip()
    if tokens_input:
        try:
            max_tokens = int(tokens_input)
        except:
            max_tokens = 4096

    return LLMConfig(
        provider=provider,
        api_base=api_base,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
