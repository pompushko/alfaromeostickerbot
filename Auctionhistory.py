from curl_cffi import requests
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup 
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s -  %(message)s'
)


async def auctionhistory_img(vin):
    lot_url = f"https://auctionhistory.io/item/{vin}"
    try:
        async with AsyncSession() as client:
            logger.info(f"URL страницы лота: {lot_url}")
            lot_response = await client.get(lot_url, impersonate="edge101")
            if lot_response.status_code != 200:
                logger.error(f"Ошибка: Страница с лотом вернула HTTP код {lot_response.status_code}")
                logger.warning(f"URL для VIN {vin} на auctionhistory не найден.")
                return [], []

            soup = BeautifulSoup(lot_response.text, "html.parser")
            image_tags = soup.find_all("img")  
            image_urls = [
                img["data-src"] for img in image_tags
                if "data-src" in img.attrs and "auctionhistory.io" in img["data-src"] and vin in img["data-src"]
            ]
            if image_urls:
                return image_urls, lot_url
            else:
                logger.warning(f"Изображения для VIN {vin} не найдены.")
            return [], lot_url
    except Exception as e:
        logger.error(f"Ошибка при запросе: {e}")
        return [], []

  