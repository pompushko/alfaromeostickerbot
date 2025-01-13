from curl_cffi import requests
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup 
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s -  %(message)s'
)


async def autotorgby_img(vin):
    lot_url = f"https://cars.autotorgby.com/istoriya-prodazh-copart-iaai-manheim?VIN={vin}"
    try:
        async with AsyncSession() as client:
            logger.info(f"URL страницы лота: {lot_url}")
            lot_response = await client.get(lot_url, impersonate="edge101")
            if lot_response.status_code != 200:
                logger.error(f"Ошибка: Страница с лотом вернула HTTP код {lot_response.status_code}")
                logger.warning(f"URL для VIN {vin} на autotorgby не найден.")
                return [], []

            soup = BeautifulSoup(lot_response.text, "html.parser")
            image_tags = soup.find_all("link", {"itemprop": "contentUrl"})
            image_urls = [
                link["href"] for link in image_tags
                if link.name == "link" and "href" in link.attrs
            ]
            if image_urls:
                return image_urls, lot_url
            else:
                logger.warning(f"Изображения для VIN {vin} не найдены.")
            return [], lot_url
    except Exception as e:
        logger.error(f"Ошибка при запросе: {e}")
        return [], []

  