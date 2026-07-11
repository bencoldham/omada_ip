import httpx
from loguru import logger as l


async def get_public_ip(timeout: int = 10):
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get("https://api.ipify.org", timeout=timeout)
                response.raise_for_status()
                return response.text
            except (httpx.HTTPError, httpx.RequestError) as e:
                l.error(f"Connection failed: {e}. Retrying immediately.")
