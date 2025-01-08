from curl_cffi import requests
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup 

async def auctionhistory_img(vin):
    lot_url = f"https://auctionhistory.io/item/{vin}"
    try:
        async with AsyncSession() as client:
            print(f"URL страницы лота: {lot_url}")
            lot_response = await client.get(lot_url, impersonate="edge101")
            if lot_response.status_code != 200:
                print(f"Ошибка: Страница с лотом вернула HTTP код {lot_response.status_code}")
                return [], lot_url

            soup = BeautifulSoup(lot_response.text, "html.parser")
            image_tags = soup.find_all("img")  
            image_urls = [
                img["data-src"] for img in image_tags
                if "data-src" in img.attrs and "auctionhistory.io" in img["data-src"] and vin in img["data-src"]
            ]
            if image_urls:
                return image_urls, lot_url
            else:
                print(f"Изображения для VIN {vin} не найдены.")

    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return []

  