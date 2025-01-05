from curl_cffi.requests import AsyncSession
import json

async def atlanticexpress_img(vin):
    scrape_ninja_url = "https://scrapeninja.p.rapidapi.com/scrape"
    headers = {
        "Content-Type": "application/json",
        "X-Rapidapi-Key": "21ad582326mshd1131edf7f568aep14a7d8jsnf62d9fdf4b90"
    }
    payload = {
        "url": f"https://atlanticexpress.com.ua/api/v2/lots/search?query={vin}&page=1",
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
            items = body.get("items", [])
            
            if not items:
                print(f"Лоты для VIN {vin} не найдены.")
                return []

            images = []
            for item in items:
                media = item.get("media", {})
                medium_images = media.get("images", {}).get("medium", [])
                images.extend(medium_images)
            
            if images:
                print(f"Найдено {len(images)} изображений для VIN {vin}.")
                return images
            else:
                print(f"Изображения для VIN {vin} не найдены.")
                return []

    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return []

