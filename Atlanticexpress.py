from curl_cffi.requests import AsyncSession
import json
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s -  %(message)s'
)

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
                logger.error(f"Ошибка: HTTP статус {response.status_code}")
                return [], []

            data = response.json()
            body = json.loads(data.get("body", "{}"))
            if not items:
                logger.warning(f"URL для VIN {vin} на atlanticexpress не найден.")
                return [], []            
            items = body.get("items", [])
            slug = body['items'][0]['slug']
            if not slug:
                logger.warning(f"URL для VIN {vin} на atlanticexpress не найден.")
                return [], []
         
            lot_url = f"https://atlanticexpress.com.ua/auction/lot/{slug}/"
            logger.info(f"URL страницы лота: {lot_url}")
            
            images = []
            for item in items:
                media = item.get("media", {})
                medium_images = media.get("images", {}).get("medium", [])
                images.extend(medium_images)
            
            if images:
                return images, lot_url
            else:
                logger.warning(f"Изображения для VIN {vin} не найдены.")
                return [], lot_url

    except Exception as e:
        logger.error(f"Ошибка при запросе: {e}")
        return [], []

