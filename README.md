[![Docker](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/pompushko/alfaromeostickerbot)

## Example of running in Docker
```yaml
  redis:
  
  alfaromeostickerbot:
    image: pompushko/alfaromeostickerbot:latest
    environment:
      - TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
      - MAX_REQUESTS_PER_DAY=5
      - SQLITE_LOCATION={mounted_dir}/VINComplectations.sqlite3
    restart: always
    deploy:
      mode: global
    volumes:
      - {dir_on_pc}:{mounted_dir}
```