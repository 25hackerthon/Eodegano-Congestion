import os
from typing import List

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from outscraper import ApiClient
from pydantic import BaseModel

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI 혼잡도 조회 및 경로 최적화 API", version="1.0")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = ApiClient(api_key=os.getenv("OUTSCRAPER_API_KEY"))

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OptimizeRouteRequest(BaseModel):
    places: List[str]

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

@app.post("/optimize_route")
async def optimize_route(request: OptimizeRouteRequest):
    try:
        places_str = ", ".join(request.places)
        prompt = f"""다음 장소들을 방문할 최적의 순서를 정해주세요. 각 장소의 혼잡도, 이동 시간, 효율성을 고려하여 가장 합리적인 경로를 제안해주세요.
        장소 목록: {places_str}

        응답은 최적화된 방문 순서를 쉼표로 구분된 문자열로만 제공해주세요.
        예시:
        장소1, 장소2, 장소3
        """

        chat_completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 여행 경로 최적화 전문가입니다. 장소의 혼잡도와 효율성을 고려하여 최적의 방문 순서를 제안합니다."},
                {"role": "user", "content": prompt}
            ]
        )

        optimized_route = chat_completion.choices[0].message.content
        return {"optimized_route": optimized_route}

    except Exception as e:
        return {"error": str(e)}