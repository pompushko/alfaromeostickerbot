from curl_cffi.requests import AsyncSession
import os 
import io


from Atlanticexpress import atlanticexpress_img
from Auctionhistory import auctionhistory_img
from Bid import bid_img


async def get_image(vin):
    resource_functions = {
        "auctionhistory": auctionhistory_img,
        "bid": bid_img,
        "atlanticexpress": atlanticexpress_img,
        }
    
    images_urls = []

    for resource_name, resource_function in resource_functions.items():
        print(f"Обрабатывается ресурс: {resource_name}")
        result = await resource_function(vin)
        current_images_urls, current_lot_url = result

        if current_images_urls:
            print(f"Найдено {len(current_images_urls)} изображений на ресурсе {resource_name}.")
            images_urls.extend(current_images_urls)
            lot_url = current_lot_url
            break  

    if not images_urls:
        print(f"Изображения для VIN {vin} не найдены ни на одном ресурсе.")
        return []
        

    try:
        async with AsyncSession() as client:
            images = []
            for idx, img_url in enumerate(images_urls):  
                try:
                    img_response = await client.get(img_url, impersonate="edge101")
                    if img_response.status_code == 200:
                        if len(img_response.content) > 0:
                            image_buffer = io.BytesIO(img_response.content)
                            image_buffer.seek(0)
                            images.append(image_buffer)
                        else:
                            print(f"Изображение пустое: {img_url}")
                    else:
                        print(f"Ошибка загрузки изображения {img_url}: статус {img_response.status_code}")
                except Exception as e:
                    print(f"Ошибка при обработке изображения {img_url}: {e}")

    except Exception as e:
        print(f"Ошибка при запросе: {e}")
        return [], lot_url
    return images, lot_url
