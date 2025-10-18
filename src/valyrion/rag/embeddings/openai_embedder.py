"""
OpenAI Embeddings Generator
"""

from typing import List, Optional
import asyncio
from openai import AsyncOpenAI
import hashlib
import logging

logger = logging.getLogger(__name__)


class OpenAIEmbedder:
    """Wrapper for OpenAI embeddings API with caching"""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        cache_client: Optional[any] = None,
        batch_size: int = 100,
    ):
        """
        Initialize OpenAI embedder

        Args:
            api_key: OpenAI API key
            model: Embedding model name
            cache_client: Redis client for caching (optional)
            batch_size: Number of texts to embed in one batch
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.cache_client = cache_client
        self.batch_size = batch_size
        self.embedding_dim = 3072 if "large" in model else 1536

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache first
        if self.cache_client:
            cache_key = self._get_cache_key(text)
            cached_embedding = await self._get_from_cache(cache_key)
            if cached_embedding:
                logger.debug("Cache hit for embedding")
                return cached_embedding

        # Generate embedding
        try:
            response = await self.client.embeddings.create(input=[text], model=self.model)
            embedding = response.data[0].embedding

            # Cache result
            if self.cache_client:
                await self._save_to_cache(cache_key, embedding, ttl=2592000)  # 30 days

            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched)

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}/{(len(texts) + self.batch_size - 1) // self.batch_size}")

            # Check cache for each text in batch
            batch_embeddings = []
            texts_to_embed = []
            text_indices = []

            for idx, text in enumerate(batch):
                if self.cache_client:
                    cache_key = self._get_cache_key(text)
                    cached_embedding = await self._get_from_cache(cache_key)
                    if cached_embedding:
                        batch_embeddings.append((idx, cached_embedding))
                        continue

                texts_to_embed.append(text)
                text_indices.append(idx)

            # Generate embeddings for non-cached texts
            if texts_to_embed:
                try:
                    response = await self.client.embeddings.create(
                        input=texts_to_embed, model=self.model
                    )
                    new_embeddings = [item.embedding for item in response.data]

                    # Cache new embeddings
                    if self.cache_client:
                        cache_tasks = []
                        for text, embedding in zip(texts_to_embed, new_embeddings):
                            cache_key = self._get_cache_key(text)
                            cache_tasks.append(
                                self._save_to_cache(cache_key, embedding, ttl=2592000)
                            )
                        await asyncio.gather(*cache_tasks)

                    # Add to batch results
                    for idx, embedding in zip(text_indices, new_embeddings):
                        batch_embeddings.append((idx, embedding))

                except Exception as e:
                    logger.error(f"Error generating batch embeddings: {e}")
                    raise

            # Sort by original index
            batch_embeddings.sort(key=lambda x: x[0])
            all_embeddings.extend([emb for _, emb in batch_embeddings])

            # Rate limiting (avoid hitting OpenAI limits)
            if i + self.batch_size < len(texts):
                await asyncio.sleep(1)  # 1 second between batches

        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{self.model}:{text_hash}"

    async def _get_from_cache(self, key: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        try:
            import json
            cached = self.cache_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    async def _save_to_cache(self, key: str, embedding: List[float], ttl: int):
        """Save embedding to cache"""
        try:
            import json
            self.cache_client.setex(key, ttl, json.dumps(embedding))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
