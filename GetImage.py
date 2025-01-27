from curl_cffi.requests import AsyncSession
import io


from Atlanticexpress import atlanticexpress_img
from Auctionhistory import auctionhistory_img
from Bid import bid_img
from Autotorgby import autotorgby_img
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s -  %(message)s'
)

async def get_image(vin):
    resource_functions = {
        "autotorgby": autotorgby_img,
        "auctionhistory": auctionhistory_img,
        "bid": bid_img,
        "atlanticexpress": atlanticexpress_img,
        }
    
    images_urls = []

    for resource_name, resource_function in resource_functions.items():
        logger.info(f"Обрабатывается ресурс: {resource_name}")
        result = await resource_function(vin)
        current_images_urls, current_lot_url = result

        if current_images_urls:
            logger.info(f"Найдено {len(current_images_urls)} изображений на ресурсе {resource_name}.")
            images_urls.extend(current_images_urls)
            lot_url = current_lot_url
            break  

    if not images_urls:
        logger.warning(f"Изображения для VIN {vin} не найдены ни на одном ресурсе.")
        lot_url = current_lot_url
        return [], lot_url
        

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
                            logger.warning(f"Изображение пустое: {img_url}")
                    else:
                        logger.error(f"Ошибка загрузки изображения {img_url}: статус {img_response.status_code}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке изображения {img_url}: {e}")

    except Exception as e:
        logger.error(f"Ошибка при запросе: {e}")
        return [], lot_url
    return images, lot_url
