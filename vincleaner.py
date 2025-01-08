# Срабатывает своя система подозрительного трафика. Пока не используем
from curl_cffi import requests
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup 

async def vincleaner_img(vin):
    lot_url = f"https://vincleaner.com/ru/vehicles/{vin}"
    try:
        async with AsyncSession() as client:
            print(f"URL страницы лота: {lot_url}")
            lot_response = await client.get(lot_url, impersonate="edge101")
            if lot_response.status_code != 200:
                print(f"Ошибка: Страница с лотом вернула HTTP код {lot_response.status_code}")
                return []

            soup = BeautifulSoup(lot_response.text, "html.parser")
            image_tags = soup.find_all("img")  
            images = []
            image_urls = [
                img["src"] 
                for img in image_tags 
                if "src" in img.attrs and "copart" in img["src"] and "alt" in img.attrs and vin in img["alt"]
            ]
            if image_urls:
                return image_urls
            else:
                print(f"Изображения для VIN {vin} не найдены.")

    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return []

  