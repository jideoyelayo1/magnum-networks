import httpx
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
import json
logging.basicConfig(level=logging.INFO)


class KalshiClient:
    """
    Kalashi Client

    """

    BASE_URL:str = "https://api.elections.kalshi.com/trade-api/v2/markets"

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10),
           stop=stop_after_attempt(5))
    async def fetch_markets(self)-> dict:
        """fetch markets data

        Returns:
            dict: Json of data
        """
        params = {
            "status": "open",
            "series_ticker": "KXNBAMVP", 
        }

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(self.BASE_URL, params=params)
            res.raise_for_status()
            return res.json()

    async def get_live_data(self)->list:
        """Get live data

        Returns:
            _type_: _description_
        """

        response = await self.fetch_markets()
        markets = response.get("markets", [])

        parsed = []

        for m in markets:
            yes_ask = m.get("yes_ask", 100) 
            yes_bid = m.get("yes_bid", 0) 

            mid_price = (yes_ask + yes_bid) / 2.0

            parsed.append({
                "source": "kalshi",
                "market_id": m.get("ticker"),
                "title": m.get("title"),
                "outcome": m.get("yes_sub_title"), 
                "price": mid_price / 100.0,        
                "volume": float(m.get("volume", 0)),
                "liquidity": float(m.get("liquidity", 0)) / 100.0 
            })
            # print(parsed[-1])
            
        return parsed
