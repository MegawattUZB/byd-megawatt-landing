# Перенос лендингов BYD Megawatt на собственный домен

Инструкция для разработчика. Время на перенос — 15–30 минут.

## Что это

Статический сайт: HTML + CSS + JS + картинки + шрифты. **Нет** бэкенда, базы данных, форм, PHP, Node.js, сборщиков. Работает на любом веб-сервере (nginx, Apache, хостинг панели, CDN, S3).

Сейчас временно опубликован на GitHub Pages: https://nematovbekk-beep.github.io/chazor/

```
/                    index.html        — выбор модели
/chazor/             index.html        — лендинг BYD Chazor
/song-plus/          index.html        — лендинг BYD Song Plus DM-i
/assets/css/         style.css
/assets/js/          app.js (калькулятор, языки, смарт-баннеры), analytics.js (счётчики)
/assets/img/         фото (webp), логотипы, превью для соцсетей (og/*.jpg)
/assets/fonts/       Conthrax woff2 (заголовки)
/tools/build.py      генератор страниц — на сервер НЕ загружать
```

Все пути внутри страниц относительные, поэтому сайт работает и в корне домена, и в подпапке — главное сохранить структуру папок.

## Куда разместить (выбрать один вариант)

1. **Поддомен (рекомендуется)** — например `promo.megawatt.uz` или `promo.byd.megawatt.uz`. Не трогает основной сайт и его CMS. Нужно: A/CNAME-запись в DNS + виртуальный хост + SSL (Let's Encrypt).
2. **Подпапка основного сайта** — например `byd.megawatt.uz/promo/`. Подходит, если основной сайт отдаёт статику с диска (nginx/Apache, WordPress, Bitrix). Не подходит для конструкторов (Tilda и т.п.) — тогда только поддомен.

Итоговые адреса, например: `https://promo.megawatt.uz/chazor/` и `https://promo.megawatt.uz/song-plus/`.

## Шаги

1. Вписать новый адрес в `tools/build.py`:
   ```python
   "url": "https://promo.megawatt.uz",   # без слэша на конце; для подпапки — с ней: https://byd.megawatt.uz/promo
   ```
   и пересобрать (нужен только Python 3, зависимостей нет):
   ```bash
   python3 tools/build.py
   ```
   Это обновит canonical, hreflang, og:url, og:image и Schema.org.
   Без Python можно заменить строку `https://nematovbekk-beep.github.io` на новый адрес во всех `index.html` (3 файла).
2. Загрузить на сервер всё, **кроме** `tools/`, `README.md`, `MIGRATION.md`.
3. Включить HTTPS (обязательно — иначе браузеры и рекламные системы ругаются).
4. Проверить по чек-листу ниже.
5. Сообщить маркетингу новые адреса — заменить ссылки в рекламных кабинетах.

## Настройки сервера (желательно)

- MIME-тип для шрифтов: `font/woff2` (на старых nginx/Apache может отсутствовать).
- Сжатие gzip/brotli для `.html`, `.css`, `.js`.
- Кеш: `assets/` — 30 дней, `*.html` — без долгого кеша (`no-cache`), чтобы правки цен были видны сразу.

Пример для nginx:
```nginx
location /assets/ { expires 30d; add_header Cache-Control "public"; }
location ~* \.html$ { add_header Cache-Control "no-cache"; }
types { font/woff2 woff2; }
```

## Аналитика

В `tools/build.py`, блок `SITE`, вписать ID и пересобрать:
`gtm_id` (GTM-XXXX) **или** `ga4_id` (G-XXXX), `fb_pixel_id`, `ym_id`.

События для целей/конверсий:
- `call_click` — клик по любой кнопке звонка (в Meta Pixel — стандартное `Contact`); параметры: `model`, `place`, `lang`, для калькулятора `calc`;
- `calc_used`, `smart_banner`, `lang_switch`, `main_site_click`.

Если используется GTM — события приходят в `dataLayer`, настроить триггеры «Пользовательское событие».

## Чек-лист проверки после переноса

- [ ] `/chazor/` и `/song-plus/` открываются по HTTPS, фото и шрифт заголовков загружаются
- [ ] Кнопка звонка на телефоне открывает набор `+998 78 113 70 88`
- [ ] Переключатель RU/UZ работает, `?lang=uz` открывает узбекскую версию
- [ ] Калькулятор считает; `/chazor/?term=12` меняет заголовок на «0% на 12 месяцев»
- [ ] Логотип ведёт на https://byd.megawatt.uz/
- [ ] Превью ссылки в Telegram показывает картинку (проверить через @WebpageBot)
- [ ] В консоли браузера нет ошибок
- [ ] Счётчики видят посещения и событие `call_click`

## После переноса

Старый адрес на GitHub Pages можно отключить, когда в рекламе заменены все ссылки (репозиторий `nematovbekk-beep.github.io` → удалить или сделать приватным).

## Как обновлять цены и тексты

Всё в одном файле `tools/build.py`: цены комплектаций, таблицы ставок, тексты RU/UZ, FAQ, адреса, телефон. После правки — `python3 tools/build.py` и загрузить изменённые `index.html`. Подробности — в `README.md`.

## Лицензия шрифта

Заголовки набраны шрифтом Conthrax (Typodermic Fonts). Для размещения на сайте нужна веб-лицензия. Если её нет — сообщить маркетингу, шрифт меняется на бесплатный аналог в одну строку в `assets/css/style.css`.
