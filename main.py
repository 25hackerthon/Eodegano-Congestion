from fastapi import FastAPI, Query
from outscraper import ApiClient
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AI 혼잡도 조회 API", version="1.0")

client = ApiClient(api_key=os.getenv("API_KEY"))

@app.get("/congestion")
def get_congestion(place: str = Query(..., description="조회할 장소 이름")):
    try:
        result = client.google_maps_search(place, limit=1, language="ko")

        if not result or not isinstance(result[0], list) or len(result[0]) == 0:
            return {"error": "장소 데이터를 불러오지 못했습니다."}

        place_data = result[0][0]

        response = {
            "name": place_data.get("name"),
            "address": place_data.get("full_address"),
            "rating": place_data.get("rating"),
            "popular_times": place_data.get("popular_times", []),
        }

        if not response["popular_times"]:
            response["message"] = "혼잡도 데이터가 없습니다."

        return response

    except Exception as e:
        return {"error": str(e)}

