from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ProviderDetail(BaseModel):
    """Model for provider details.

    Attributes:
        id: Unique identifier for the provider
        name: Display name for the provider
        description: Description of the provider
        url: URL to the provider's platform
        requiredCredentials: List of required credential keys
    """

    id: str = Field(..., description="Unique identifier for the provider")
    name: str = Field(..., description="Display name for the provider")
    description: str = Field(..., description="Description of the provider")
    url: str = Field(..., description="URL to the provider's platform")
    requiredCredentials: List[str] = Field(..., description="List of required credential keys")
    recommended: bool = Field(
        False,
        description="Whether the provider is recommended for use in Local Operator",
    )


SupportedHostingProviders = [
    ProviderDetail(
        id="openai",
        name="OpenAI",
        description="OpenAI's API provides access to GPT-4o and other models",
        url="https://platform.openai.com/",
        requiredCredentials=["OPENAI_API_KEY"],
        recommended=True,
    ),
    ProviderDetail(
        id="anthropic",
        name="Anthropic",
        description="Anthropic's Claude models for AI assistants",
        url="https://www.anthropic.com/",
        requiredCredentials=["ANTHROPIC_API_KEY"],
        recommended=True,
    ),
    ProviderDetail(
        id="google",
        name="Google",
        description="Google's Gemini models for multimodal AI capabilities",
        url="https://ai.google.dev/",
        requiredCredentials=["GOOGLE_AI_STUDIO_API_KEY"],
        recommended=True,
    ),
    ProviderDetail(
        id="mistral",
        name="Mistral AI",
        description="Mistral AI's open and proprietary language models",
        url="https://mistral.ai/",
        requiredCredentials=["MISTRAL_API_KEY"],
        recommended=True,
    ),
    ProviderDetail(
        id="ollama",
        name="Ollama",
        description="Run open-source large language models locally",
        url="https://ollama.ai/",
        requiredCredentials=[],
        recommended=False,
    ),
    ProviderDetail(
        id="openrouter",
        name="OpenRouter",
        description="Access to multiple AI models through a unified API",
        url="https://openrouter.ai/",
        requiredCredentials=["OPENROUTER_API_KEY"],
        recommended=True,
    ),
    ProviderDetail(
        id="deepseek",
        name="DeepSeek",
        description="DeepSeek's language models for various AI applications",
        url="https://deepseek.ai/",
        requiredCredentials=["DEEPSEEK_API_KEY"],
        recommended=True,
    ),
    ProviderDetail(
        id="kimi",
        name="Kimi",
        description="Moonshot AI's Kimi models for Chinese and English language tasks",
        url="https://moonshot.cn/",
        requiredCredentials=["KIMI_API_KEY"],
        recommended=False,
    ),
    ProviderDetail(
        id="alibaba",
        name="Alibaba Cloud",
        description="Alibaba's Qwen models for natural language processing",
        url="https://www.alibabacloud.com/",
        requiredCredentials=["ALIBABA_CLOUD_API_KEY"],
        recommended=True,
    ),
]
"""List of supported model hosting providers.

This list contains the names of all supported AI model hosting providers that can be used
with the Local Operator API. Each provider has its own set of available models and pricing.

The supported providers are:
- anthropic: Anthropic's Claude models
- ollama: Local model hosting with Ollama
- deepseek: DeepSeek's language models
- google: Google's Gemini models
- openai: OpenAI's GPT models
- openrouter: OpenRouter model aggregator
- alibaba: Alibaba's Qwen models
- kimi: Kimi AI's models
- mistral: Mistral AI's models
"""

RecommendedOpenRouterModelIds = [
    "google/gemini-2.0-flash-001",
    "anthropic/claude-3.7-sonnet",
    "anthropic/claude-3.5-sonnet",
    "openai/chatgpt-4o-latest",
    "openai/gpt-4o-2024-11-20",
    "openai/gpt-4o",
    "qwen/qwen-plus",
    "qwen/qwen-max",
    "mistralai/mistral-large-2411",
    "mistralai/mistral-large-2407",
    "mistralai/mistral-large",
]
"""List of recommended model IDs from OpenRouter.

This list contains the model IDs of recommended models available through the OpenRouter
provider. These models are selected based on performance, reliability, and community
feedback. The IDs follow the format 'provider/model-name' as used by OpenRouter's API.

The list includes models from various providers:
- Google's Gemini models
- Anthropic's Claude models
- OpenAI's GPT models
- Qwen models
- Mistral AI models
"""


class ModelInfo(BaseModel):
    """
    Represents the pricing information for a given model.

    Attributes:
        input_price (float): Cost per million input tokens.
        output_price (float): Cost per million output tokens.
        max_tokens (Optional[int]): Maximum number of tokens supported by the model.
        context_window (Optional[int]): Context window size of the model.
        supports_images (Optional[bool]): Whether the model supports images.
        supports_prompt_cache (bool): Whether the model supports prompt caching.
        cache_writes_price (Optional[float]): Cost per million tokens for cache writes.
        cache_reads_price (Optional[float]): Cost per million tokens for cache reads.
        description (Optional[str]): Description of the model.
        recommended (Optional[bool]): Whether the model is recommended for use in Local
        Operator.  This is determined based on community usage and feedback.
    """

    input_price: float = 0.0
    output_price: float = 0.0
    max_tokens: Optional[int] = None
    context_window: Optional[int] = None
    supports_images: Optional[bool] = None
    supports_prompt_cache: bool = False
    cache_writes_price: Optional[float] = None
    cache_reads_price: Optional[float] = None
    description: str = Field(..., description="Description of the model")
    id: str = Field(..., description="Unique identifier for the model")
    name: str = Field(..., description="Display name for the model")
    recommended: bool = Field(
        False,
        description=(
            "Whether the model is recommended for use in Local Operator. "
            "This is determined based on community usage and feedback."
        ),
    )

    @field_validator("input_price", "output_price")
    def price_must_be_non_negative(cls, value: float) -> float:
        """Validates that the price is non-negative."""
        if value < 0:
            raise ValueError("Price must be non-negative.")
        return value


def get_model_info(hosting: str, model: str) -> ModelInfo:
    """
    Retrieves the model information based on the hosting provider and model name.

    This function checks a series of known hosting providers and their associated
    models to return a `ModelInfo` object containing relevant details such as
    pricing, context window, and image support. If the hosting provider is not
    supported, a ValueError is raised. If the model is not found for a supported
    hosting provider, a default `unknown_model_info` is returned.

    Args:
        hosting (str): The hosting provider name (e.g., "openai", "google").
        model (str): The model name (e.g., "gpt-3.5-turbo", "gemini-1.0-pro").

    Returns:
        ModelInfo: The model information for the specified hosting and model.
                   Returns `unknown_model_info` if the model is not found for a
                   supported hosting provider.

    Raises:
        ValueError: If the hosting provider is unsupported.
    """
    model_info = unknown_model_info

    if hosting == "anthropic":
        if model in anthropic_models:
            model_info = anthropic_models[model]
    elif hosting == "ollama":
        return ollama_default_model_info
    elif hosting == "deepseek":
        if model in deepseek_models:
            return deepseek_models[model]
    elif hosting == "google":
        if model in google_models:
            return google_models[model]
    elif hosting == "openai":
        return openai_models[model]
    elif hosting == "openrouter":
        return openrouter_default_model_info
    elif hosting == "alibaba":
        if model in qwen_models:
            return qwen_models[model]
    elif hosting == "kimi":
        if model in kimi_models:
            return kimi_models[model]
    elif hosting == "mistral":
        if model in mistral_models:
            return mistral_models[model]
    else:
        raise ValueError(f"Unsupported hosting provider: {hosting}")

    return model_info


unknown_model_info: ModelInfo = ModelInfo(
    id="unknown",
    name="Unknown",
    max_tokens=-1,
    context_window=-1,
    supports_images=False,
    supports_prompt_cache=False,
    input_price=0.0,
    output_price=0.0,
    description="Unknown model with default settings",
    recommended=False,
)
"""
Default ModelInfo when model is unknown.

This ModelInfo is returned by `get_model_info` when a specific model
is not found within a supported hosting provider's catalog. It provides
a fallback with negative max_tokens and context_window to indicate
the absence of specific model details.
"""

anthropic_models: Dict[str, ModelInfo] = {
    "claude-3-7-sonnet-latest": ModelInfo(
        id="claude-3-7-sonnet-latest",
        name="Claude 3.7 Sonnet (Latest)",
        max_tokens=8192,
        context_window=200_000,
        supports_images=True,
        supports_prompt_cache=True,
        input_price=3.0,
        output_price=15.0,
        cache_writes_price=3.75,
        cache_reads_price=3.0,
        description=(
            "Anthropic's latest and most powerful model for coding and agentic "
            "tasks.  Latest version."
        ),
        recommended=True,
    ),
    "claude-3-7-sonnet-20250219": ModelInfo(
        id="claude-3-7-sonnet-20250219",
        name="Claude 3.7 Sonnet (2025-02-19)",
        max_tokens=8192,
        context_window=200_000,
        supports_images=True,
        supports_prompt_cache=True,
        input_price=3.0,
        output_price=15.0,
        cache_writes_price=3.75,
        cache_reads_price=3.0,
        description=(
            "Anthropic's latest and most powerful model for coding and agentic "
            "tasks.  Snapshot from February 2025."
        ),
        recommended=True,
    ),
    "claude-3-5-sonnet-20241022": ModelInfo(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        max_tokens=8192,
        context_window=200_000,
        supports_images=True,
        supports_prompt_cache=True,
        input_price=3.0,
        output_price=15.0,
        cache_writes_price=3.75,
        cache_reads_price=3.0,
        description="Anthropic's latest balanced model with excellent performance",
        recommended=True,
    ),
    "claude-3-5-haiku-20241022": ModelInfo(
        id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku (2024-10-22)",
        max_tokens=8192,
        context_window=200_000,
        supports_images=False,
        supports_prompt_cache=True,
        input_price=0.8,
        output_price=4.0,
        cache_writes_price=1.0,
        cache_reads_price=0.8,
        description="Fast and efficient model for simpler tasks",
        recommended=False,
    ),
    "claude-3-opus-20240229": ModelInfo(
        id="claude-3-opus-20240229",
        name="Claude 3 Opus (2024-02-29)",
        max_tokens=4096,
        context_window=200_000,
        supports_images=True,
        supports_prompt_cache=True,
        input_price=15.0,
        output_price=75.0,
        cache_writes_price=18.75,
        cache_reads_price=1.5,
        description="Anthropic's most powerful model for complex tasks",
        recommended=False,
    ),
    "claude-3-haiku-20240307": ModelInfo(
        id="claude-3-haiku-20240307",
        name="Claude 3 Haiku (2024-03-07)",
        max_tokens=4096,
        context_window=200_000,
        supports_images=True,
        supports_prompt_cache=True,
        input_price=0.25,
        output_price=1.25,
        cache_writes_price=0.3,
        cache_reads_price=0.3,
        description="Fast and efficient model for simpler tasks",
        recommended=False,
    ),
}

# TODO: Add fetch for token, context window, image support
ollama_default_model_info: ModelInfo = ModelInfo(
    max_tokens=-1,
    context_window=-1,
    supports_images=False,
    supports_prompt_cache=False,
    input_price=0.0,
    output_price=0.0,
    description="Local model hosting with Ollama",
    id="ollama",
    name="Ollama",
    recommended=False,
)

# TODO: Add fetch for token, context window, image support
openrouter_default_model_info: ModelInfo = ModelInfo(
    max_tokens=-1,
    context_window=-1,
    supports_images=False,
    supports_prompt_cache=False,
    input_price=0.0,
    output_price=0.0,
    cache_writes_price=0.0,
    cache_reads_price=0.0,
    description="Access to various AI models from different providers through a single API",
    id="openrouter",
    name="OpenRouter",
    recommended=False,
)

openai_models: Dict[str, ModelInfo] = {
    "gpt-4-turbo-preview": ModelInfo(
        max_tokens=128_000,
        context_window=128_000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=10.0,
        output_price=30.0,
        description="Capable GPT-4 model, optimized for speed. Currently points to "
        "gpt-4-0125-preview.",
        id="gpt-4-turbo-preview",
        name="GPT-4 Turbo",
        recommended=False,
    ),
    "gpt-4-vision-preview": ModelInfo(
        max_tokens=128_000,
        context_window=128_000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=10.0,
        output_price=30.0,
        description="GPT-4 Turbo with the ability to understand images",
        id="gpt-4-vision-preview",
        name="GPT-4 Vision",
        recommended=False,
    ),
    "gpt-4": ModelInfo(
        max_tokens=8192,
        context_window=4096,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=30.0,
        output_price=60.0,
        description="More capable than any GPT-3.5 model, able to do more complex tasks",
        id="gpt-4",
        name="GPT-4",
        recommended=False,
    ),
    "gpt-3.5-turbo": ModelInfo(
        max_tokens=16385,
        context_window=16385,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.5,
        output_price=1.5,
        description="Most capable GPT-3.5 model, optimized for chat at 1/10th the cost of GPT-4",
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        recommended=False,
    ),
    "gpt-3.5-turbo-16k": ModelInfo(
        max_tokens=16385,
        context_window=16385,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=1.0,
        output_price=2.0,
        description="Same capabilities as standard GPT-3.5 Turbo but with longer context",
        id="gpt-3.5-turbo-16k",
        name="GPT-3.5 Turbo 16K",
        recommended=False,
    ),
    "gpt-4o": ModelInfo(
        max_tokens=16384,
        context_window=128000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.5,
        output_price=10.0,
        description="Optimized GPT-4 model with improved performance and reliability",
        id="gpt-4o",
        name="GPT-4o",
        recommended=True,
    ),
    "gpt-4o-mini": ModelInfo(
        max_tokens=16384,
        context_window=200000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.15,
        output_price=0.6,
        description="Smaller optimized GPT-4 model with good balance of performance and cost",
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        recommended=False,
    ),
    "o3-mini": ModelInfo(
        max_tokens=100000,
        context_window=200000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=1.1,
        output_price=4.4,
        description="Reasoning model with advanced capabilities on math, science, and coding.",
        id="o3-mini",
        name="o3 Mini",
        recommended=True,
    ),
    "o3-mini-high": ModelInfo(
        max_tokens=100000,
        context_window=200000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=1.1,
        output_price=4.4,
        description="Reasoning model with advanced capabilities on math, science, and "
        "coding pre-set to highest reasoning effort.",
        id="o3-mini-high",
        name="o3 Mini High",
        recommended=False,
    ),
    "o1-preview": ModelInfo(
        max_tokens=32768,
        context_window=128000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=15.0,
        output_price=60.0,
        description="Preview version of O1 model with multimodal capabilities",
        id="o1-preview",
        name="o1 Preview",
        recommended=False,
    ),
    "o1": ModelInfo(
        max_tokens=100000,
        context_window=200000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=15.0,
        output_price=60.0,
        description="Advanced reasoning model with high performance on math, science, and "
        "coding tasks.",
        id="o1",
        name="o1",
        recommended=False,
    ),
    "o1-mini": ModelInfo(
        max_tokens=65536,
        context_window=128000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=1.1,
        output_price=4.4,
        description="Compact version of O1 model with high performance on math, science, "
        "and coding tasks.",
        id="o1-mini",
        name="o1 Mini",
        recommended=False,
    ),
    "gpt-4.5": ModelInfo(
        max_tokens=16000,
        context_window=128000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=75.0,
        output_price=150.0,
        description="Latest GPT series model, great for creative and complex tasks",
        id="gpt-4.5",
        name="GPT 4.5",
        recommended=False,
    ),
}


google_models: Dict[str, ModelInfo] = {
    "gemini-2.0-flash-001": ModelInfo(
        max_tokens=8192,
        context_window=1_048_576,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0.1,
        output_price=0.4,
        description="Google's latest multimodal model with excellent performance",
        id="gemini-2.0-flash-001",
        name="Gemini 2.0 Flash",
        recommended=True,
    ),
    "gemini-2.0-flash-lite-preview-02-05": ModelInfo(
        id="gemini-2.0-flash-lite-preview-02-05",
        name="Gemini 2.0 Flash Lite Preview",
        max_tokens=8192,
        context_window=1_048_576,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Lighter version of Gemini 2.0 Flash",
        recommended=False,
    ),
    "gemini-2.0-pro-exp-02-05": ModelInfo(
        id="gemini-2.0-pro-exp-02-05",
        name="Gemini 2.0 Pro Exp",
        max_tokens=8192,
        context_window=2_097_152,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Google's most powerful Gemini model",
        recommended=False,
    ),
    "gemini-2.0-flash-thinking-exp-01-21": ModelInfo(
        id="gemini-2.0-flash-thinking-exp-01-21",
        name="Gemini 2.0 Flash Thinking Exp",
        max_tokens=65_536,
        context_window=1_048_576,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Experimental Gemini model with thinking capabilities",
        recommended=False,
    ),
    "gemini-2.0-flash-thinking-exp-1219": ModelInfo(
        id="gemini-2.0-flash-thinking-exp-1219",
        name="Gemini 2.0 Flash Thinking Exp",
        max_tokens=8192,
        context_window=32_767,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Experimental Gemini model with thinking capabilities",
        recommended=False,
    ),
    "gemini-2.0-flash-exp": ModelInfo(
        id="gemini-2.0-flash-exp",
        name="Gemini 2.0 Flash Exp",
        max_tokens=8192,
        context_window=1_048_576,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Experimental version of Gemini 2.0 Flash",
        recommended=False,
    ),
    "gemini-1.5-flash-002": ModelInfo(
        id="gemini-1.5-flash-002",
        name="Gemini 1.5 Flash 002",
        max_tokens=8192,
        context_window=1_048_576,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Fast and efficient multimodal model",
        recommended=False,
    ),
    "gemini-1.5-flash-exp-0827": ModelInfo(
        id="gemini-1.5-flash-exp-0827",
        name="Gemini 1.5 Flash Exp 0827",
        max_tokens=8192,
        context_window=1_048_576,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0,
        output_price=0,
        description="Experimental version of Gemini 1.5 Flash",
        recommended=False,
    ),
}

deepseek_models: Dict[str, ModelInfo] = {
    "deepseek-chat": ModelInfo(
        id="deepseek-chat",
        name="Deepseek Chat",
        max_tokens=8_192,
        context_window=64_000,
        supports_images=False,
        supports_prompt_cache=True,
        input_price=0.27,
        output_price=1.1,
        cache_writes_price=0.14,
        cache_reads_price=0.014,
        description="General purpose chat model",
        recommended=True,
    ),
    "deepseek-reasoner": ModelInfo(
        id="deepseek-reasoner",
        name="Deepseek Reasoner",
        max_tokens=8_000,
        context_window=64_000,
        supports_images=False,
        supports_prompt_cache=True,
        input_price=0.55,
        output_price=2.19,
        cache_writes_price=0.55,
        cache_reads_price=0.14,
        description="Specialized for complex reasoning tasks",
        recommended=False,
    ),
}

qwen_models: Dict[str, ModelInfo] = {
    "qwen2.5-coder-32b-instruct": ModelInfo(
        id="qwen2.5-coder-32b-instruct",
        name="Qwen 2.5 Coder 32B Instruct",
        max_tokens=8_192,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.0,
        output_price=6.0,
        cache_writes_price=2.0,
        cache_reads_price=6.0,
        description="Specialized for code generation and understanding",
        recommended=False,
    ),
    "qwen2.5-coder-14b-instruct": ModelInfo(
        id="qwen2.5-coder-14b-instruct",
        name="Qwen 2.5 Coder 14B Instruct",
        max_tokens=8_192,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.0,
        output_price=6.0,
        cache_writes_price=2.0,
        cache_reads_price=6.0,
        description="Medium-sized code-specialized model",
        recommended=False,
    ),
    "qwen2.5-coder-7b-instruct": ModelInfo(
        id="qwen2.5-coder-7b-instruct",
        name="Qwen 2.5 Coder 7B Instruct",
        max_tokens=8_192,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.5,
        output_price=1.0,
        cache_writes_price=0.5,
        cache_reads_price=1.0,
        description="Efficient code-specialized model",
        recommended=False,
    ),
    "qwen2.5-coder-3b-instruct": ModelInfo(
        id="qwen2.5-coder-3b-instruct",
        name="Qwen 2.5 Coder 3B Instruct",
        max_tokens=8_192,
        context_window=32_768,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.5,
        output_price=1.0,
        cache_writes_price=0.5,
        cache_reads_price=1.0,
        description="Compact code-specialized model",
        recommended=False,
    ),
    "qwen2.5-coder-1.5b-instruct": ModelInfo(
        id="qwen2.5-coder-1.5b-instruct",
        name="Qwen 2.5 Coder 1.5B Instruct",
        max_tokens=8_192,
        context_window=32_768,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.0,
        output_price=0.0,
        cache_writes_price=0.0,
        cache_reads_price=0.0,
        description="Very compact code-specialized model",
        recommended=False,
    ),
    "qwen2.5-coder-0.5b-instruct": ModelInfo(
        id="qwen2.5-coder-0.5b-instruct",
        name="Qwen 2.5 Coder 0.5B Instruct",
        max_tokens=8_192,
        context_window=32_768,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.0,
        output_price=0.0,
        cache_writes_price=0.0,
        cache_reads_price=0.0,
        description="Smallest code-specialized model",
        recommended=False,
    ),
    "qwen-coder-plus-latest": ModelInfo(
        id="qwen-coder-plus-latest",
        name="Qwen Coder Plus Latest",
        max_tokens=129_024,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=3.5,
        output_price=7,
        cache_writes_price=3.5,
        cache_reads_price=7,
        description="Advanced code generation model",
        recommended=False,
    ),
    "qwen-plus-latest": ModelInfo(
        id="qwen-plus-latest",
        name="Qwen Plus Latest",
        max_tokens=129_024,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.8,
        output_price=2,
        cache_writes_price=0.8,
        cache_reads_price=0.2,
        description="Balanced performance Qwen model",
        recommended=True,
    ),
    "qwen-turbo-latest": ModelInfo(
        id="qwen-turbo-latest",
        name="Qwen Turbo Latest",
        max_tokens=1_000_000,
        context_window=1_000_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.8,
        output_price=2,
        cache_writes_price=0.8,
        cache_reads_price=2,
        description="Fast and efficient Qwen model",
        recommended=False,
    ),
    "qwen-max-latest": ModelInfo(
        id="qwen-max-latest",
        name="Qwen Max Latest",
        max_tokens=30_720,
        context_window=32_768,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.4,
        output_price=9.6,
        cache_writes_price=2.4,
        cache_reads_price=9.6,
        description="Alibaba's most powerful Qwen model",
        recommended=False,
    ),
    "qwen-coder-plus": ModelInfo(
        id="qwen-coder-plus",
        name="Qwen Coder Plus",
        max_tokens=129_024,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=3.5,
        output_price=7,
        cache_writes_price=3.5,
        cache_reads_price=7,
        description="Advanced code generation model",
        recommended=False,
    ),
    "qwen-plus": ModelInfo(
        id="qwen-plus",
        name="Qwen Plus",
        max_tokens=129_024,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.8,
        output_price=2,
        cache_writes_price=0.8,
        cache_reads_price=0.2,
        description="Balanced performance Qwen model",
        recommended=True,
    ),
    "qwen-turbo": ModelInfo(
        id="qwen-turbo",
        name="Qwen Turbo",
        max_tokens=1_000_000,
        context_window=1_000_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.3,
        output_price=0.6,
        cache_writes_price=0.3,
        cache_reads_price=0.6,
        description="Fast and efficient Qwen model",
        recommended=False,
    ),
    "qwen-max": ModelInfo(
        id="qwen-max",
        name="Qwen Max",
        max_tokens=30_720,
        context_window=32_768,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.4,
        output_price=9.6,
        cache_writes_price=2.4,
        cache_reads_price=9.6,
        description="Alibaba's most powerful Qwen model",
        recommended=True,
    ),
    "qwen-vl-max": ModelInfo(
        id="qwen-vl-max",
        name="Qwen VL Max",
        max_tokens=30_720,
        context_window=32_768,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=3,
        output_price=9,
        cache_writes_price=3,
        cache_reads_price=9,
        description="Multimodal Qwen model with vision capabilities",
        recommended=False,
    ),
    "qwen-vl-max-latest": ModelInfo(
        id="qwen-vl-max-latest",
        name="Qwen VL Max Latest",
        max_tokens=129_024,
        context_window=131_072,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=3,
        output_price=9,
        cache_writes_price=3,
        cache_reads_price=9,
        description="Multimodal Qwen model with vision capabilities",
        recommended=False,
    ),
    "qwen-vl-plus": ModelInfo(
        id="qwen-vl-plus",
        name="Qwen VL Plus",
        max_tokens=6_000,
        context_window=8_000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=1.5,
        output_price=4.5,
        cache_writes_price=1.5,
        cache_reads_price=4.5,
        description="Balanced multimodal Qwen model",
        recommended=False,
    ),
    "qwen-vl-plus-latest": ModelInfo(
        id="qwen-vl-plus-latest",
        name="Qwen VL Plus Latest",
        max_tokens=129_024,
        context_window=131_072,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=1.5,
        output_price=4.5,
        cache_writes_price=1.5,
        cache_reads_price=4.5,
        description="Balanced multimodal Qwen model",
        recommended=False,
    ),
}

mistral_models: Dict[str, ModelInfo] = {
    "mistral-large-latest": ModelInfo(
        id="mistral-large-latest",
        name="Mistral Large Latest",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.0,
        output_price=6.0,
        description="Mistral's most powerful model.  Latest version.",
        recommended=False,
    ),
    "mistral-large-2411": ModelInfo(
        id="mistral-large-2411",
        name="Mistral Large 2411",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=2.0,
        output_price=6.0,
        description="Mistral's most powerful model.  Snapshot from November 2024.",
        recommended=False,
    ),
    "pixtral-large-2411": ModelInfo(
        id="pixtral-large-2411",
        name="Pixtral Large 2411",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=2.0,
        output_price=6.0,
        description="Mistral's multimodal model with image capabilities",
        recommended=False,
    ),
    "ministral-3b-2410": ModelInfo(
        id="ministral-3b-2410",
        name="Ministral 3B 2410",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.04,
        output_price=0.04,
        description="Compact 3B parameter model for efficient inference",
        recommended=False,
    ),
    "ministral-8b-2410": ModelInfo(
        id="ministral-8b-2410",
        name="Ministral 8B 2410",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.1,
        output_price=0.1,
        description="Medium-sized 8B parameter model balancing performance and efficiency",
        recommended=False,
    ),
    "mistral-small-2501": ModelInfo(
        id="mistral-small-2501",
        name="Mistral Small 2501",
        max_tokens=32_000,
        context_window=32_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.1,
        output_price=0.3,
        description="Fast and efficient model for simpler tasks",
        recommended=False,
    ),
    "pixtral-12b-2409": ModelInfo(
        id="pixtral-12b-2409",
        name="Pixtral 12B 2409",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=0.15,
        output_price=0.15,
        description="12B parameter multimodal model with vision capabilities",
        recommended=False,
    ),
    "open-mistral-nemo-2407": ModelInfo(
        id="open-mistral-nemo-2407",
        name="Open Mistral Nemo 2407",
        max_tokens=131_000,
        context_window=131_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.15,
        output_price=0.15,
        description="Open-source version of Mistral optimized with NVIDIA NeMo",
        recommended=False,
    ),
    "open-codestral-mamba": ModelInfo(
        id="open-codestral-mamba",
        name="Open Codestral Mamba",
        max_tokens=256_000,
        context_window=256_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.15,
        output_price=0.15,
        description="Open-source code-specialized model using Mamba architecture",
        recommended=False,
    ),
    "codestral-2501": ModelInfo(
        id="codestral-2501",
        name="Codestral 2501",
        max_tokens=256_000,
        context_window=256_000,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=0.3,
        output_price=0.9,
        description="Specialized for code generation and understanding",
        recommended=False,
    ),
}


YUAN_TO_USD = 0.14

kimi_models: Dict[str, ModelInfo] = {
    "moonshot-v1-8k": ModelInfo(
        id="moonshot-v1-8k",
        name="Moonshot V1 8K",
        max_tokens=8192,
        context_window=8192,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=12.00 * YUAN_TO_USD,
        output_price=12.00 * YUAN_TO_USD,
        cache_writes_price=24.00 * YUAN_TO_USD,
        cache_reads_price=0.02 * YUAN_TO_USD,
        description="General purpose language model with 8K context",
        recommended=False,
    ),
    "moonshot-v1-32k": ModelInfo(
        id="moonshot-v1-32k",
        name="Moonshot V1 32K",
        max_tokens=8192,
        context_window=32_768,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=24.00 * YUAN_TO_USD,
        output_price=24.00 * YUAN_TO_USD,
        cache_writes_price=24.00 * YUAN_TO_USD,
        cache_reads_price=0.02 * YUAN_TO_USD,
        description="General purpose language model with 32K context",
        recommended=False,
    ),
    "moonshot-v1-128k": ModelInfo(
        id="moonshot-v1-128k",
        name="Moonshot V1 128K",
        max_tokens=8192,
        context_window=131_072,
        supports_images=False,
        supports_prompt_cache=False,
        input_price=60.00 * YUAN_TO_USD,
        output_price=60.00 * YUAN_TO_USD,
        cache_writes_price=24.00 * YUAN_TO_USD,
        cache_reads_price=0.02 * YUAN_TO_USD,
        description="General purpose language model with 128K context",
        recommended=False,
    ),
    "moonshot-v1-8k-vision-preview": ModelInfo(
        id="moonshot-v1-8k-vision-preview",
        name="Moonshot V1 8K Vision Preview",
        max_tokens=8192,
        context_window=8192,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=12.00 * YUAN_TO_USD,
        output_price=12.00 * YUAN_TO_USD,
        cache_writes_price=24.00 * YUAN_TO_USD,
        cache_reads_price=0.02 * YUAN_TO_USD,
        description="Multimodal model with 8K context",
        recommended=False,
    ),
    "moonshot-v1-32k-vision-preview": ModelInfo(
        id="moonshot-v1-32k-vision-preview",
        name="Moonshot V1 32K Vision Preview",
        max_tokens=8192,
        context_window=32_768,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=24.00 * YUAN_TO_USD,
        output_price=24.00 * YUAN_TO_USD,
        cache_writes_price=24.00 * YUAN_TO_USD,
        cache_reads_price=0.02 * YUAN_TO_USD,
        description="Multimodal model with 32K context",
        recommended=False,
    ),
    "moonshot-v1-128k-vision-preview": ModelInfo(
        id="moonshot-v1-128k-vision-preview",
        name="Moonshot V1 128K Vision Preview",
        max_tokens=8192,
        context_window=131_072,
        supports_images=True,
        supports_prompt_cache=False,
        input_price=60.00 * YUAN_TO_USD,
        output_price=60.00 * YUAN_TO_USD,
        cache_writes_price=24.00 * YUAN_TO_USD,
        cache_reads_price=0.02 * YUAN_TO_USD,
        description="Multimodal model with 128K context",
        recommended=False,
    ),
}
