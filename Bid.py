from curl_cffi.requests import AsyncSession
import json
from bs4 import BeautifulSoup

async def bid_img(vin):
    scrape_ninja_url = "https://scrapeninja.p.rapidapi.com/scrape"
    headers = {
        "Content-Type": "application/json",
        "X-Rapidapi-Key": "21ad582326mshd1131edf7f568aep14a7d8jsnf62d9fdf4b90"
    }
    payload = {
        "url": f"https://bid.cars/app/search/en/vin-lot/{vin}/false",
        "geo": "us"
    }

    try:
        async with AsyncSession() as client:
            response = await client.post(scrape_ninja_url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"Ошибка: HTTP статус {response.status_code}")
                return []

            data = response.json()
            body = json.loads(data.get("body", "{}"))
            lot_url = body.get("url", None)            
            if not lot_url or "lot" not in lot_url:
                print("URL для Vin на bid.cars не найден.")
                return [], lot_url

            print(f"URL страницы лота: {lot_url}")

            lot_response = await client.get(lot_url, impersonate="edge101")
            if lot_response.status_code != 200:
                print(f"Ошибка: Страница с лотом вернула HTTP код {lot_response.status_code}")
                return [], lot_url

            soup = BeautifulSoup(lot_response.text, "html.parser")
            image_tags = soup.find_all("img")

            image_urls = [
                img["src"] for img in image_tags
                if "src" in img.attrs and "mercury.bid.cars" in img["src"] and vin in img["src"]
            ]
            
            if image_urls:
                return image_urls, lot_url
            else:
                print(f"Изображения для VIN {vin} не найдены.")

    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return []

