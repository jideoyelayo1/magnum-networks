import httpx
from tenacity import retry, wait_exponential, stop_after_attempt
import json

    
class PolymarketClient:
    # Notice the change in BASE_URL to the slug lookup endpoint
    BASE_URL = "https://gamma-api.polymarket.com/events/slug"

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(5))
    async def fetch_event_by_slug(self, slug="nba-mvp-694"):
        # The slug is passed directly in the URL path for this endpoint
        url = f"{self.BASE_URL}/{slug}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url)
            
            if res.status_code == 404:
                print(f"Error: Slug '{slug}' not found. Verify the URL on Polymarket.")
                return None
                
            res.raise_for_status()
            return res.json()

    async def get_live_data(self):
        # Fetch using the slug you see in your browser
        event = await self.fetch_event_by_slug("nba-mvp-694")
        
        if not event:
            return []

        # Polymarket 'Events' contain a list of 'Markets' (one for each player)
        markets = event.get("markets", [])
        parsed = []

        for m in markets:
            prices_raw = m.get("outcomePrices")
            outcomes_raw = m.get("outcomes")
            
            if not prices_raw or not outcomes_raw:
                continue

            try:
                # Handle potential stringified JSON from the API
                prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
                outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw
                
                for i, outcome_name in enumerate(outcomes):
                    data_point = {
                        "source": "polymarket",
                        "market_id": str(m.get("id")),
                        "title": m.get("question"),
                        "outcome": outcome_name,
                        "price": float(prices[i]),
                        "volume": float(m.get("volume", 0) or 0),
                    }
                    parsed.append(data_point)
                    # print(f"Parsed: {data_point['title']} - {data_point['outcome']}: {data_point['price']}")
                    
            except Exception as e:
                continue
    
        return parsed