"""
Multi-provider model client management.
"""
import logging
from typing import Dict, Optional
from autogen_core.models import ChatCompletionClient
from models.config import ConfigLoader

logger = logging.getLogger(__name__)


class ModelProviderManager:
    """Manages multiple model providers and clients."""
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Initialize the model provider manager."""
        self.config_loader = config_loader or ConfigLoader()
        self._clients: Dict[str, ChatCompletionClient] = {}
        self._fallback_order = ["deepseek", "openai", "moonshot", "alibaba"]
    
    async def get_client(self, model_name: str) -> ChatCompletionClient:
        """Get or create a model client for the specified model."""
        if model_name not in self._clients:
            await self._create_client(model_name)
        return self._clients[model_name]
    
    async def _create_client(self, model_name: str) -> None:
        """Create a new model client."""
        try:
            model_config = self.config_loader.get_model_config(model_name)
            client_config = model_config.get_client_config()
            
            # Create client using AutoGen's load_component method
            client = ChatCompletionClient.load_component(client_config)
            self._clients[model_name] = client
            
            logger.info(f"Created model client for {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to create client for {model_name}: {e}")
            raise
    
    async def get_client_with_fallback(self, preferred_model: str) -> ChatCompletionClient:
        """Get a model client with fallback to other providers."""
        # Try preferred model first
        try:
            return await self.get_client(preferred_model)
        except Exception as e:
            logger.warning(f"Failed to get preferred model {preferred_model}: {e}")
        
        # Try fallback models
        for fallback_model in self._fallback_order:
            if fallback_model == preferred_model:
                continue  # Skip the already failed model
            
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                return await self.get_client(fallback_model)
            except Exception as e:
                logger.warning(f"Fallback model {fallback_model} also failed: {e}")
                continue
        
        raise RuntimeError("All model providers failed")
    
    def clear_cache(self):
        """Clear the client cache."""
        self._clients.clear()
        logger.info("Model client cache cleared")
    
    def list_available_models(self) -> list[str]:
        """List all available model configurations."""
        models_config = self.config_loader.load_models_config()
        return list(models_config.keys())
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all configured model providers."""
        health_status = {}
        models_config = self.config_loader.load_models_config()
        
        for model_name in models_config.keys():
            try:
                await self.get_client(model_name)
                # Attempt a simple test (this would need to be implemented based on client capabilities)
                health_status[model_name] = True
            except Exception as e:
                logger.error(f"Health check failed for {model_name}: {e}")
                health_status[model_name] = False
        
        return health_status


# Global model provider manager instance
_model_manager: Optional[ModelProviderManager] = None


def get_model_manager() -> ModelProviderManager:
    """Get the global model provider manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelProviderManager()
    return _model_manager


async def get_model_client(model_name: str) -> ChatCompletionClient:
    """Convenience function to get a model client."""
    manager = get_model_manager()
    return await manager.get_client(model_name)