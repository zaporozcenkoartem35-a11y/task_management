

import httpx


async def fetch_random_quote() -> str:
    url = "https://zenquotes.io/api/random"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                response_data = response.json()
                if response_data and isinstance(response_data, list):
                    quote = response_data[0].get("q")
                    author = response_data[0].get("a")
                    if author != 'Unknown':
                        return f'{quote} - {author}'
                    return f"{quote}"
    except Exception as e:
        print(f"Failed to fetch quote: {e}")

    return 'Today without a quote('