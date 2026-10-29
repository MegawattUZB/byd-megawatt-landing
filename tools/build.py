#!/usr/bin/env python3
"""Собирает статические лендинги BYD Megawatt.

Запуск:  python3 tools/build.py
Результат: index.html, chazor/index.html, song-plus/index.html

Все цены, ставки, тексты RU/UZ и настройки — в этом файле (блоки SITE, COMMON, MODELS).
"""
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- настройки
SITE = {
    # Домен без слэша на конце, например "https://promo.byd-megawatt.uz".
    # Пока пусто — canonical, hreflang и og:url не выводятся.
    "url": "https://nematovbekk-beep.github.io",
    "phone": "+998781137088",
    "phone_display": "+998 78 113 70 88",
    # Аналитика: впишите ID — счётчики подключатся автоматически.
    "gtm_id": "",          # GTM-XXXXXXX
    "ga4_id": "",          # G-XXXXXXXXXX (если без GTM)
    "fb_pixel_id": "",     # 1234567890
    "ym_id": "",           # 12345678
    # YouTube: ID ролика (часть ссылки после watch?v=). Пусто — блок скрыт.
    "video_review_id": "",  # обзор Вадима Суцепина
    "video_client_id": "",  # отзыв клиента
    "theme_color": "#0e0e10",
    # Куда ведёт клик по логотипу (открывается в новой вкладке, лендинг остаётся открытым)
    "main_site": "https://byd.megawatt.uz/",
    # Откуда страницы в Тильде берут картинки, шрифты, CSS и JS (jsDelivr поверх GitHub).
    # После изменения файлов в assets/ — новый тег в репозитории (v2, v3…), обновить здесь и пересобрать.
    "cdn": "https://cdn.jsdelivr.net/gh/MegawattUZB/byd-megawatt-landing@v1",
}

# Реальные отзывы клиентов. Пока список пуст — блок на сайте не выводится.
# Формат: {"name": "Азиз", "model": "Chazor", "ru": "Текст отзыва", "uz": "Fikr matni", "time": "14:32"}
REVIEWS = []

TERMS = [12, 18, 24, 30, 36, 48, 60]
DOWNS = [25, 30, 40, 50, 60]

# Ставки по таблице «Осенняя акция» (годовые, %). Строки — взнос из DOWNS, столбцы — срок из TERMS.
RATES_CHAZOR_55 = [
    [0, 0, 4.8, 7.8, 8.8, 9.9, 11],
    [0, 0, 4, 7, 8, 8.9, 10],
    [0, 0, 0, 5, 6, 7.9, 9],
    [0, 0, 0, 0, 2, 5, 6],
    [0, 0, 0, 0, 0, 1, 3],
]
RATES_FLAGSHIP = [  # Chazor 120KM Flagship и Song Plus DM-i — одинаковые
    [0, 3, 6.5, 10.5, 10.8, 12.4, 13.2],
    [0, 1.4, 5, 9, 9.5, 11.2, 12.2],
    [0, 0, 1.9, 6, 6.9, 9.2, 10.3],
    [0, 0, 0, 2.3, 3.6, 6.2, 7.7],
    [0, 0, 0, 0, 0.5, 1.6, 3.5],
]

ADDRESSES = [
    ("BYD Megawatt Suntown",
     "г. Ташкент, 1,5 км от поста ГАИ, п. Солнечный",
     "Toshkent sh., YPX postidan 1,5 km, Solnechniy"),
    ("BYD Megawatt Tashkent City Mall",
     "г. Ташкент, ТЦ Tashkent City Mall, 1-й этаж",
     "Toshkent sh., Tashkent City Mall SM, 1-qavat"),
    ("BYD Megawatt Navoi 35",
     "г. Ташкент, ул. Алишера Навои, 35",
     "Toshkent sh., Alisher Navoiy ko‘chasi, 35"),
    ("BYD Megawatt ТРЦ Next",
     "г. Ташкент, ул. Бобура, 6",
     "Toshkent sh., Bobur ko‘chasi, 6"),
]

# ---------------------------------------------------------------- общие тексты
COMMON = {
    "call": ("Позвонить", "Qo‘ng‘iroq qilish"),
    "callShort": ("Позвонить · 0%", "Qo‘ng‘iroq · 0%"),
    "dealer": ("Официальный дилер BYD", "BYD rasmiy dileri"),
    "promo": ("Осенняя акция", "Kuzgi aksiya"),
    "heroCta": ("Позвонить и узнать условия", "Qo‘ng‘iroq qilib, shartlarni bilish"),
    "heroNote": ("Ответим за 10 секунд", "10 soniyada javob beramiz"),
    "payFrom": ("Платёж от", "Oylik to‘lov — eng kami"),
    "perMonth": ("сум/мес", "so‘m/oy"),
    "b1t": ("0% переплаты", "0% ortiqcha to‘lov"),
    "b1d": ("Платите ровно стоимость автомобиля", "Faqat avtomobil narxini to‘laysiz"),
    "b3t": ("Взнос от 25%", "Boshlang‘ich to‘lov 25% dan"),
    "b3d": ("Чем больше взнос — тем дольше срок 0%", "To‘lov qancha ko‘p bo‘lsa, 0% muddati shuncha uzun"),
    "b4t": ("Гарантия 6 лет", "6 yil kafolat"),
    "b4d": ("И 8 лет на батарею", "Batareyaga esa 8 yil"),
    "calcTitle": ("Рассчитайте платёж за 10 секунд", "To‘lovni 10 soniyada hisoblang"),
    "calcLead": ("Выберите комплектацию, первый взнос и срок — увидите платёж в месяц.",
                 "Komplektatsiya, boshlang‘ich to‘lov va muddatni tanlang — oylik to‘lovni ko‘rasiz."),
    "tabInst": ("Рассрочка 0%", "0% muddatli to‘lov"),
    "tabCredit": ("Кредит", "Kredit"),
    "trim": ("Комплектация", "Komplektatsiya"),
    "down": ("Первый взнос", "Boshlang‘ich to‘lov"),
    "term": ("Срок, мес", "Muddat, oy"),
    "monthly": ("Ежемесячный платёж", "Oylik to‘lov"),
    "downSum": ("Первый взнос", "Boshlang‘ich to‘lov"),
    "loanSum": ("Сумма финансирования", "Moliyalashtirish summasi"),
    "rate": ("Ставка", "Stavka"),
    "overpay": ("Переплата", "Ortiqcha to‘lov"),
    "noOverpay": ("без переплаты", "ortiqcha to‘lovsiz"),
    "sum": ("сум", "so‘m"),
    "mo": ("мес", "oy"),
    "hintUp": ("Увеличьте взнос до {p}% — и рассрочка 0% станет доступна на {m} мес.",
               "Boshlang‘ich to‘lovni {p}% gacha oshiring — 0% muddat {m} oyga uzayadi."),
    "hintMax": ("Максимальный срок рассрочки 0% при этом взносе — {m} мес. Дольше — во вкладке «Кредит».",
                "Ushbu to‘lovda 0% muddatning eng ko‘pi — {m} oy. Uzoqroq muddat — «Kredit» bo‘limida."),
    "banks": ("Банки-партнёры", "Hamkor banklar"),
    "calcCta": ("Зафиксировать этот расчёт", "Ushbu hisob-kitobni band qilish"),
    "calcNote": ("Расчёт предварительный и не является офертой. Точные условия зависят от банка — уточняйте у менеджера.",
                 "Hisob-kitob taxminiy va oferta hisoblanmaydi. Aniq shartlar bankka bog‘liq — menejerdan aniqlang."),
    "testDrive": ("Записаться на тест-драйв", "Test-drayvga yozilish"),
    "compareTitle": ("Сравните комплектации", "Komplektatsiyalarni solishtiring"),
    "price": ("Цена", "Narxi"),
    "videoTitle": ("Смотрите сами", "O‘zingiz ko‘ring"),
    "videoReview": ("Обзор от Вадима Суцепина", "Vadim Sutsepin sharhi"),
    "videoClient": ("Отзыв владельца", "Egasining fikri"),
    "whyTitle": ("Почему BYD Megawatt", "Nega BYD Megawatt"),
    "w1t": ("Официальный дилер BYD", "BYD rasmiy dileri"),
    "w1d": ("Новые автомобили с официальной гарантией производителя",
            "Ishlab chiqaruvchining rasmiy kafolati bilan yangi avtomobillar"),
    "w2t": ("6 лет гарантии на авто", "Avtomobilga 6 yil kafolat"),
    "w2d": ("И 8 лет гарантии на высоковольтную батарею",
            "Yuqori voltli batareyaga esa 8 yil kafolat"),
    "w3t": ("Оформим в банке за вас", "Bankda biz rasmiylashtiramiz"),
    "w3d": ("Подберём банк-партнёра и условия под ваш бюджет",
            "Byudjetingizga mos hamkor bank va shartlarni tanlaymiz"),
    "w4t": ("4 салона в Ташкенте", "Toshkentda 4 ta salon"),
    "w4d": ("Приезжайте в ближайший — посмотреть и прокатиться",
            "Eng yaqiniga keling — ko‘rib, haydab ko‘ring"),
    "stepsTitle": ("Как купить в 3 шага", "3 qadamda xarid"),
    "s1t": ("Позвоните", "Qo‘ng‘iroq qiling"),
    "s1d": ("Менеджер подберёт банк и условия под ваш бюджет",
            "Menejer byudjetingizga mos bank va shartlarni tanlaydi"),
    "s2t": ("Приезжайте в салон", "Salonga keling"),
    "s2d": ("С паспортом — оформим договор на месте",
            "Pasport bilan — shartnomani joyida tuzamiz"),
    "s3t": ("Уезжайте на новом BYD", "Yangi BYD bilan qayting"),
    "s3d": ("Без переплаты — по рассрочке 0%",
            "Ortiqcha to‘lovsiz — 0% muddatli to‘lov bilan"),
    "faqTitle": ("Частые вопросы", "Ko‘p beriladigan savollar"),
    "q1": ("Что значит рассрочка 0%?", "0% muddatli to‘lov nima degani?"),
    "a1": ("Вы платите только стоимость автомобиля — без процентов. Срок рассрочки 0% зависит от первого взноса: чем больше взнос, тем дольше срок. Посчитайте в калькуляторе выше.",
           "Siz faqat avtomobil narxini to‘laysiz — foizsiz. 0% muddati boshlang‘ich to‘lovga bog‘liq: to‘lov qancha ko‘p bo‘lsa, muddat shuncha uzun. Yuqoridagi kalkulyatorda hisoblang."),
    "q2": ("Какие документы нужны?", "Qanday hujjatlar kerak?"),
    "a2": ("Для оформления нужен паспорт (ID-карта). Точный список зависит от выбранного банка — менеджер подскажет по телефону.",
           "Rasmiylashtirish uchun pasport (ID-karta) kerak. Aniq ro‘yxat tanlangan bankka bog‘liq — menejer telefonda aytib beradi."),
    "q3": ("Какая гарантия?", "Kafolat qanday?"),
    "a3": ("6 лет на автомобиль и 8 лет на высоковольтную батарею. Обслуживание — у официального дилера BYD Megawatt.",
           "Avtomobilga 6 yil va yuqori voltli batareyaga 8 yil. Xizmat ko‘rsatish — BYD Megawatt rasmiy dilerida."),
    "q4": ("Нужно ли заряжать гибрид от розетки?", "Gibridni rozetkadan quvvatlash shartmi?"),
    "a4": ("Не обязательно. DM-i заряжает батарею на ходу — от двигателя и при торможении. Зарядка от розетки просто позволит больше ездить на электричестве и экономить на топливе.",
           "Shart emas. DM-i batareyani yurish paytida — dvigateldan va tormozlashda quvvatlaydi. Rozetkadan quvvatlash esa elektrda ko‘proq yurish va yoqilg‘ini tejash imkonini beradi."),
    "q5": ("Можно ли приехать на тест-драйв?", "Test-drayvga kelsa bo‘ladimi?"),
    "a5": ("Да. Позвоните — менеджер запишет вас на удобное время в ближайший салон.",
           "Ha. Qo‘ng‘iroq qiling — menejer sizni qulay vaqtga eng yaqin salonga yozib qo‘yadi."),
    "q6": ("До какого числа действует акция?", "Aksiya qachongacha amal qiladi?"),
    "a6": ("Осенняя акция действует ограниченное время. О её завершении банк объявит отдельно — актуальные условия уточняйте по телефону.",
           "Kuzgi aksiya cheklangan muddatda amal qiladi. Tugashi alohida e’lon qilinadi — joriy shartlarni telefon orqali aniqlang."),
    "finalTitle": ("Зафиксируйте 0% сегодня", "0% ni bugun band qiling"),
    "finalText": ("Осенняя акция действует ограниченное время. Позвоните — менеджер рассчитает платёж под ваш бюджет.",
                  "Kuzgi aksiya cheklangan muddatda amal qiladi. Qo‘ng‘iroq qiling — menejer byudjetingizga mos to‘lovni hisoblaydi."),
    "addrTitle": ("Наши салоны", "Bizning salonlar"),
    "legal": ("Информация на сайте не является публичной офертой. Финансирование предоставляют банки-партнёры; рассрочка 0% — финансирование по ставке 0% годовых при соблюдении условий банка. Цены указаны в сумах и могут быть изменены. Запас хода и расход — по данным производителя (WLTC/NEDC), фактические значения зависят от условий эксплуатации.",
              "Saytdagi ma’lumotlar ommaviy oferta hisoblanmaydi. Moliyalashtirishni hamkor banklar taqdim etadi; 0% muddatli to‘lov — bank shartlariga rioya qilingan holda yillik 0% stavkali moliyalashtirish. Narxlar so‘mda ko‘rsatilgan va o‘zgarishi mumkin. Yurish masofasi va sarf — ishlab chiqaruvchi ma’lumotlari (WLTC/NEDC), haqiqiy ko‘rsatkichlar foydalanish sharoitiga bog‘liq."),
    # смарт-баннер: подстановки {model} {term} {months} {down} {trim} {rate} {tail}
    "sTitleInst": ("{model} в&nbsp;рассрочку <em>0%</em> на&nbsp;<em>{term}&nbsp;{months}</em>",
                   "{model} — <em>{term}&nbsp;oy</em>ga <em>0%</em> muddatli to‘lov"),
    "sSubInst": ("Без переплаты. Первый взнос от {down}%. {tail}",
                 "Ortiqcha to‘lovsiz. Boshlang‘ich to‘lov {down}% dan. {tail}"),
    "sFootInst": ("*{trim}, взнос {down}%, {term} мес, 0%. Условия банков-партнёров.",
                  "*{trim}, {down}% boshlang‘ich to‘lov, {term} oy, 0%. Hamkor banklar shartlari."),
    "sTitleDown": ("{model}: первый взнос <em>{down}%</em> и&nbsp;рассрочка <em>0%</em>",
                   "{model}: boshlang‘ich to‘lov <em>{down}%</em> va <em>0%</em> muddatli to‘lov"),
    "sSubDown": ("Без переплаты — до {term}&nbsp;{months}. {tail}",
                 "Ortiqcha to‘lovsiz — {term}&nbsp;oygacha. {tail}"),
    "sTitleCredit": ("{model} в&nbsp;кредит на&nbsp;<em>{term}&nbsp;{months}</em>",
                     "{model} — <em>{term}&nbsp;oy</em>ga kredit"),
    "sSubCredit": ("Ставка от {rate}% при взносе {down}%. {tail}",
                   "{down}% boshlang‘ich to‘lovda stavka {rate}% dan. {tail}"),
    "sFootCredit": ("*{trim}, взнос {down}%, {term} мес, ставка {rate}%. Условия банков-партнёров.",
                    "*{trim}, {down}% boshlang‘ich to‘lov, {term} oy, stavka {rate}%. Hamkor banklar shartlari."),
    "monthsFew": ("месяца", "oy"),
    "monthsMany": ("месяцев", "oy"),
    # пример диалога
    "chatTitle": ("Как проходит покупка", "Xarid qanday o‘tadi"),
    "chatLabel": ("Пример диалога с менеджером", "Menejer bilan muloqot namunasi"),
    "chatManager": ("Менеджер BYD Megawatt", "BYD Megawatt menejeri"),
    "chatOnline": ("онлайн", "onlayn"),
    "c3": ("А какие документы нужны?", "Qanday hujjatlar kerak?"),
    "c4": ("Паспорт — остальное подскажем под выбранный банк и оформим в салоне. Когда удобно подъехать на тест-драйв?",
           "Pasport — qolganini tanlangan bank bo‘yicha aytib, salonda rasmiylashtiramiz. Test-drayvga qachon kelish qulay?"),
    "c5": ("Завтра после обеда", "Ertaga tushdan keyin"),
    "c6": ("Записал вас на завтра, 15:00 ✅ Машина будет готова к поездке.",
           "Sizni ertaga soat 15:00 ga yozdim ✅ Avtomobil sinovga tayyor bo‘ladi."),
    "chatCta": ("Есть вопрос? Позвоните", "Savol bormi? Qo‘ng‘iroq qiling"),
    "reviewsTitle": ("Отзывы владельцев", "Egalarining fikrlari"),
    "choose": ("Выберите модель", "Modelni tanlang"),
    "more": ("Подробнее", "Batafsil"),
    "yes": ("✓", "✓"),
    "no": ("—", "—"),
}

# ---------------------------------------------------------------- модели
MODELS = {
    "chazor": {
        "name": "BYD Chazor",
        "short": "Chazor",
        "hero_img": "1",
        "gallery": ["9", "6", "5", "2", "3", "4", "7", "8"],
        "trims": [
            {"id": "55", "name": "55KM Luxe", "price": 255_900_000, "rates": RATES_CHAZOR_55,
             "banks": ["Ipoteka Bank", "OFB", "InfinBank", "BRB"]},
            {"id": "120", "name": "120KM Flagship", "price": 315_200_000, "rates": RATES_FLAGSHIP,
             "banks": ["Ipoteka Bank", "OFB"]},
        ],
        "t": {
            "metaTitle": ("BYD Chazor в рассрочку 0% до 36 месяцев — BYD Megawatt",
                          "BYD Chazor — 36 oygacha 0% muddatli to‘lov — BYD Megawatt"),
            "metaDesc": ("BYD Chazor — гибрид DM-i, 3,8 л на 100 км. Рассрочка 0% до 36 месяцев, взнос от 25%. Официальный дилер BYD Megawatt в Ташкенте. Звоните: +998 78 113 70 88.",
                         "BYD Chazor — DM-i gibrid, 100 km ga 3,8 l. 36 oygacha 0% muddatli to‘lov, boshlang‘ich to‘lov 25% dan. Toshkentdagi BYD Megawatt rasmiy dileri. Qo‘ng‘iroq qiling: +998 78 113 70 88."),
            "heroTitle": ("BYD Chazor в&nbsp;рассрочку <em>0%</em> на&nbsp;<em>36&nbsp;месяцев</em>",
                          "BYD Chazor — <em>36&nbsp;oygacha</em> <em>0%</em> muddatli to‘lov"),
            "heroSub": ("Без переплаты. Первый взнос от 25%. Гибрид с расходом 3,8&nbsp;л на 100&nbsp;км.",
                        "Ortiqcha to‘lovsiz. Boshlang‘ich to‘lov 25% dan. 100&nbsp;km ga 3,8&nbsp;l sarflaydigan gibrid."),
            "heroFoot": ("*Chazor 55KM Luxe, взнос 60%, 36 мес, 0%. Условия банков-партнёров.",
                         "*Chazor 55KM Luxe, 60% boshlang‘ich to‘lov, 36 oy, 0%. Hamkor banklar shartlari."),
            "heroTail": ("Гибрид с расходом 3,8&nbsp;л на 100&nbsp;км.", "100&nbsp;km ga 3,8&nbsp;l sarflaydigan gibrid."),
            "c1": ("Здравствуйте! Сколько будет платёж за Chazor в рассрочку?",
                   "Assalomu alaykum! Chazor muddatli to‘lovga oyiga qancha bo‘ladi?"),
            "b2t": ("До 36 месяцев", "36 oygacha"),
            "b2d": ("Удобный платёж под ваш бюджет", "Byudjetingizga mos qulay to‘lov"),
            "featTitle": ("Почему выбирают BYD Chazor", "Nega BYD Chazor tanlashadi"),
            "f1t": ("3,8 л на 100 км", "100 km ga 3,8 l"),
            "f1d": ("Гибрид DM-i: экономичный мотор 1.5 л + электромотор", "DM-i gibrid: tejamkor 1.5 l dvigatel + elektromotor"),
            "f2t": ("До 120 км на электричестве", "Elektrda 120 km gacha"),
            "f2d": ("По городу — без бензина (NEDC, 120KM Flagship)", "Shahar bo‘ylab — benzinsiz (NEDC, 120KM Flagship)"),
            "f3t": ("0–100 км/ч за 7,3 с", "0–100 km/soat 7,3 s da"),
            "f3d": ("Электромотор 145 кВт — уверенный разгон на трассе", "145 kVt elektromotor — trassada ishonchli tezlanish"),
            "f4t": ("Поворотный экран 12,8″", "12,8″ aylanuvchi ekran"),
            "f4d": ("Голосовой ассистент, 4G, обновления по воздуху", "Ovozli yordamchi, 4G, havo orqali yangilanish"),
            "f5t": ("Камера 360° и ассистенты", "360° kamera va yordamchilar"),
            "f5d": ("Адаптивный круиз, удержание в полосе, автоторможение (120KM Flagship)",
                    "Adaptiv kruiz, qatorni ushlab turish, avtotormoz (120KM Flagship)"),
            "f6t": ("Бизнес-седан 4,78 м", "4,78 m biznes-sedan"),
            "f6d": ("Колёсная база 2718 мм — просторно на заднем ряду", "G‘ildirak bazasi 2718 mm — orqa qatorda keng"),
        },
        "compare": [
            (("Запас хода на электричестве (NEDC)", "Elektrda yurish masofasi (NEDC)"), ("55 км", "55 km"), ("120 км", "120 km")),
            (("Батарея", "Batareya"), ("8,3 кВт·ч", "8,3 kVt·soat"), ("18,3 кВт·ч", "18,3 kVt·soat")),
            (("Разгон 0–100 км/ч", "0–100 km/soat tezlanish"), ("7,9 с", "7,9 s"), ("7,3 с", "7,3 s")),
            (("Камера 360°", "360° kamera"), "yes", "yes"),
            (("Адаптивный круиз и ассистенты", "Adaptiv kruiz va yordamchilar"), "no", "yes"),
            (("Подогрев сидений", "O‘rindiqlar isitgichi"), "no", "yes"),
            (("Беспроводная зарядка телефона", "Telefonni simsiz quvvatlash"), "no", "yes"),
            (("Питание приборов от авто (V2L)", "Avtomobildan qurilmalarni quvvatlash (V2L)"), "no", "yes"),
            (("Динамики", "Dinamiklar"), ("6", "6"), ("8", "8")),
        ],
    },
    "song-plus": {
        "name": "BYD Song Plus DM-i",
        "short": "Song Plus DM-i",
        "hero_img": "1",
        "gallery": ["2", "3", "4", "5", "6", "7", "8", "9", "10"],
        "trims": [
            {"id": "110", "name": "110KM Flagship", "price": 387_200_000, "rates": RATES_FLAGSHIP,
             "banks": ["Ipoteka Bank", "OFB"]},
            {"id": "150", "name": "150KM Flagship", "price": 409_700_000, "rates": RATES_FLAGSHIP,
             "banks": ["Ipoteka Bank", "OFB"]},
        ],
        "t": {
            "metaTitle": ("BYD Song Plus DM-i в рассрочку 0% до 30 месяцев — BYD Megawatt",
                          "BYD Song Plus DM-i — 30 oygacha 0% muddatli to‘lov — BYD Megawatt"),
            "metaDesc": ("BYD Song Plus DM-i Champion — кроссовер-гибрид от 4,5 л на 100 км. Рассрочка 0% до 30 месяцев, взнос от 25%. Официальный дилер BYD Megawatt в Ташкенте. Звоните: +998 78 113 70 88.",
                         "BYD Song Plus DM-i Champion — 100 km ga 4,5 l dan sarflaydigan krossover-gibrid. 30 oygacha 0% muddatli to‘lov, boshlang‘ich to‘lov 25% dan. Toshkentdagi BYD Megawatt rasmiy dileri. Qo‘ng‘iroq qiling: +998 78 113 70 88."),
            "heroTitle": ("BYD Song Plus <span class='nw'>DM-i</span> в&nbsp;рассрочку <em>0%</em> на&nbsp;<em>30&nbsp;месяцев</em>",
                          "BYD Song Plus <span class='nw'>DM-i</span> — <em>30&nbsp;oygacha</em> <em>0%</em> muddatli to‘lov"),
            "heroSub": ("Без переплаты. Первый взнос от 25%. Кроссовер-гибрид с панорамной крышей.",
                        "Ortiqcha to‘lovsiz. Boshlang‘ich to‘lov 25% dan. Panorama tomli krossover-gibrid."),
            "heroFoot": ("*Song Plus DM-i 110KM Flagship, взнос 60%, 30 мес, 0%. Условия банков-партнёров.",
                         "*Song Plus DM-i 110KM Flagship, 60% boshlang‘ich to‘lov, 30 oy, 0%. Hamkor banklar shartlari."),
            "heroTail": ("Кроссовер-гибрид с панорамной крышей.", "Panorama tomli krossover-gibrid."),
            "c1": ("Здравствуйте! Сколько будет платёж за Song Plus в рассрочку?",
                   "Assalomu alaykum! Song Plus muddatli to‘lovga oyiga qancha bo‘ladi?"),
            "b2t": ("До 30 месяцев", "30 oygacha"),
            "b2d": ("Удобный платёж под ваш бюджет", "Byudjetingizga mos qulay to‘lov"),
            "featTitle": ("Почему выбирают BYD Song Plus <span class='nw'>DM-i</span>", "Nega BYD Song Plus <span class='nw'>DM-i</span> tanlashadi"),
            "f1t": ("От 4,5 л на 100 км", "100 km ga 4,5 l dan"),
            "f1d": ("Гибрид DM-i: мотор 1.5 л + электромотор, даже при низком заряде", "DM-i gibrid: 1.5 l dvigatel + elektromotor, hatto past quvvatda ham"),
            "f2t": ("Панорамная крыша", "Panorama tom"),
            "f2d": ("С электроприводом и шторкой, 19″ литые диски", "Elektr yuritmali va pardali, 19″ quyma disklar"),
            "f3t": ("Вентиляция и подогрев сидений", "O‘rindiqlar ventilyatsiyasi va isitgichi"),
            "f3d": ("Электрорегулировка водителя в 8 направлениях", "Haydovchi o‘rindig‘i 8 yo‘nalishda elektr sozlanadi"),
            "f4t": ("Экран до 15,6″", "15,6″ gacha ekran"),
            "f4d": ("Голосовой ассистент «Hi, BYD», 4G, обновления по воздуху", "«Hi, BYD» ovozli yordamchisi, 4G, havo orqali yangilanish"),
            "f5t": ("Камера 360° и ассистенты", "360° kamera va yordamchilar"),
            "f5d": ("Адаптивный круиз, удержание в полосе, автоторможение", "Adaptiv kruiz, qatorni ushlab turish, avtotormoz"),
            "f6t": ("Электропривод багажника", "Yukxona eshigi elektr yuritmali"),
            "f6d": ("И питание бытовых приборов от машины (V2L)", "Va maishiy qurilmalarni avtomobildan quvvatlash (V2L)"),
        },
        "compare": [
            (("Батарея", "Batareya"), ("18,3 кВт·ч", "18,3 kVt·soat"), ("26,6 кВт·ч", "26,6 kVt·soat")),
            (("Расход при низком заряде", "Past quvvatdagi sarf"), ("4,5 л/100 км", "4,5 l/100 km"), ("4,6 л/100 км", "4,6 l/100 km")),
            (("Центральный экран", "Markaziy ekran"), ("12,8″", "12,8″"), ("15,6″", "15,6″")),
            (("Аудиосистема", "Audiotizim"), ("9 динамиков", "9 ta dinamik"), ("Infinity, 10 динамиков", "Infinity, 10 ta dinamik")),
            (("Зарядка от сети (AC)", "Tarmoqdan quvvatlash (AC)"), ("3,3 кВт", "3,3 kVt"), ("7 кВт", "7 kVt")),
            (("Беспроводная зарядка телефона", "Telefonni simsiz quvvatlash"), "no", "yes"),
            (("Контроль слепых зон", "Ko‘r zonalar nazorati"), "no", "yes"),
            (("Панорамная крыша, 19″ диски", "Panorama tom, 19″ disklar"), "yes", "yes"),
            (("Разгон 0–100 км/ч", "0–100 km/soat tezlanish"), ("8,3 с", "8,3 s"), ("8,3 с", "8,3 s")),
        ],
    },
}


# ---------------------------------------------------------------- расчёты
def zero_terms(rates_row):
    return [t for t, r in zip(TERMS, rates_row) if r == 0]


def min_installment(model):
    """Минимальный платёж рассрочки 0% по модели (округлён вверх до 1000)."""
    best = None
    for trim in model["trims"]:
        for i, d in enumerate(DOWNS):
            terms = zero_terms(trim["rates"][i])
            if not terms:
                continue
            pay = trim["price"] * (100 - d) / 100 / max(terms)
            if best is None or pay < best:
                best = pay
    return math.ceil(best / 1000) * 1000


def max_zero_term(model):
    return max(max(zero_terms(row)) for trim in model["trims"] for row in trim["rates"])


def fmt(n):
    return f"{n:,}".replace(",", " ")


# ---------------------------------------------------------------- шаблон
ICONS = {
    "phone": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>',
    "fuel": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16M3 21h13M7 8h5M15 10h2a2 2 0 0 1 2 2v5a1.5 1.5 0 0 0 3 0V9l-3-3"/></svg>',
    "bolt": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>',
    "speed": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 14l4-4M3.5 18a9.5 9.5 0 1 1 17 0"/></svg>',
    "screen": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/></svg>',
    "car": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 17H3v-5l2-5h14l2 5v5h-2M5 12h14"/><circle cx="7.5" cy="17" r="2"/><circle cx="16.5" cy="17" r="2"/></svg>',
    "percent": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 5 5 19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>',
    "calendar": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
    "wallet": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h13v4"/><path d="M3 7v11a2 2 0 0 0 2 2h15V9H5a2 2 0 0 1-2-2z"/><circle cx="16" cy="14.5" r="1.2"/></svg>',
    "badge": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="9" r="6"/><path d="m8.5 14-1.5 8 5-3 5 3-1.5-8"/></svg>',
    "bank": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 10 12 4l9 6M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 21h18"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    "play": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>',
    "seat": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h4l1 9h6a2 2 0 0 1 2 2v3H8z"/><path d="M8 17v4M18 17v4"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="18" height="12" rx="2"/><path d="M7 7l2-3h6l2 3"/><path d="M8 12h8"/></svg>',
    "trunk": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 16V9l3-4h12l3 4v7z"/><path d="M3 16h18M8 20v-4M16 20v-4M10 11h4"/></svg>',
}

FEATURE_ICONS = {
    "chazor": ["fuel", "bolt", "speed", "screen", "shield", "car"],
    "song-plus": ["fuel", "sun", "seat", "screen", "shield", "trunk"],
}


def page(slug):
    m = MODELS[slug]
    dict_ru, dict_uz = {}, {}

    def reg(key, pair):
        dict_ru[key], dict_uz[key] = pair
        return pair[0]

    for k, v in COMMON.items():
        reg(k, v)
    for k, v in m["t"].items():
        reg(k, v)

    def T(key):  # RU-текст для разметки (data-i18n подставит UZ)
        return dict_ru[key]

    def el(tag, key, cls="", attrs=""):
        c = f' class="{cls}"' if cls else ""
        return f'<{tag}{c} data-i18n="{key}"{attrs}>{T(key)}</{tag}>'

    tel = f"tel:{SITE['phone']}"
    min_pay = min_installment(m)
    max_term = max_zero_term(m)

    def call_btn(key, where, cls="btn btn--red"):
        return (f'<a class="{cls}" href="{tel}" data-call="{where}">{ICONS["phone"]}'
                f'<span data-i18n="{key}">{T(key)}</span></a>')

    # --- сравнение
    rows = []
    for i, (label, a, b) in enumerate(m["compare"]):
        cells = []
        for j, v in enumerate((a, b)):
            if v in ("yes", "no"):
                cls = "yes" if v == "yes" else "no"
                cells.append(f'<td class="{cls}">{"✓" if v == "yes" else "—"}</td>')
            else:
                key = f"cmp{i}{'ab'[j]}"
                reg(key, v)
                cells.append(f'<td data-i18n="{key}">{v[0]}</td>')
        key = f"cmp{i}"
        reg(key, label)
        rows.append(f'<tr><th scope="row" data-i18n="{key}">{label[0]}</th>{"".join(cells)}</tr>')
    t0, t1 = m["trims"]
    compare_html = (
        '<table class="compare"><thead><tr><th></th>'
        f'<th scope="col">{t0["name"]}</th><th scope="col">{t1["name"]}</th></tr></thead><tbody>'
        f'<tr class="compare__price"><th scope="row" data-i18n="price">{T("price")}</th>'
        f'<td>{fmt(t0["price"])}</td><td>{fmt(t1["price"])}</td></tr>'
        + "".join(rows) + "</tbody></table>"
    )

    # --- фичи
    feats = "".join(
        f'<li class="feat">{ICONS[ic]}<div><h3 data-i18n="f{i}t">{T(f"f{i}t")}</h3>'
        f'<p data-i18n="f{i}d">{T(f"f{i}d")}</p></div></li>'
        for i, ic in enumerate(FEATURE_ICONS[slug], 1)
    )

    def srcset(n):
        widths = [w for w in (800, 1200, 1600) if (ROOT / f"assets/img/{slug}/{n}-{w}.webp").exists()]
        return ", ".join(f"../assets/img/{slug}/{n}-{w}.webp {w}w" for w in widths)

    def picture(n, alt, cls="", eager=False, sizes="100vw"):
        load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
        return (f'<img class="{cls}" src="../assets/img/{slug}/{n}-1200.webp" '
                f'srcset="{srcset(n)}" '
                f'sizes="{sizes}" width="1200" height="900" alt="{html.escape(alt)}" {load}>')

    gallery = "".join(
        f'<li>{picture(n, m["name"], sizes="(min-width: 900px) 33vw, 85vw")}</li>' for n in m["gallery"]
    )

    # --- видео
    videos = []
    for vid_key, title_key in (("video_review_id", "videoReview"), ("video_client_id", "videoClient")):
        vid = SITE[vid_key]
        if vid:
            videos.append(
                f'<figure class="video"><button class="video__btn" data-yt="{html.escape(vid)}" '
                f'style="background-image:url(https://i.ytimg.com/vi/{html.escape(vid)}/hqdefault.jpg)" '
                f'aria-label="{T(title_key)}">{ICONS["play"]}</button>'
                f'<figcaption data-i18n="{title_key}">{T(title_key)}</figcaption></figure>'
            )
    video_section = ""
    if videos:
        video_section = (f'<section class="section" id="video"><div class="wrap">'
                         f'{el("h2", "videoTitle", "h2")}<div class="videos">{"".join(videos)}</div></div></section>')

    # --- адреса
    addr_items = []
    for i, (name, ru, uz) in enumerate(ADDRESSES):
        reg(f"addr{i}", (ru, uz))
        addr_items.append(f'<li>{ICONS["pin"]}<div><b>{html.escape(name)}</b>'
                          f'<span data-i18n="addr{i}">{ru}</span></div></li>')

    # --- пример диалога (ответ менеджера считается по реальным ставкам)
    t0 = m["trims"][0]
    d50 = DOWNS.index(50)
    term50 = max(zero_terms(t0["rates"][d50]))
    pay50 = math.ceil(t0["price"] * 0.5 / term50 / 1000) * 1000
    reg("c2", (
        f"Здравствуйте! {t0['name']}: при взносе 50% — {fmt(pay50)} сум в месяц на {term50} месяцев, без переплаты 👍",
        f"Assalomu alaykum! {t0['name']}: 50% boshlang‘ich to‘lovda — oyiga {fmt(pay50)} so‘m, {term50} oy, ortiqcha to‘lovsiz 👍",
    ))
    bubbles = [("in", "c1", "10:02"), ("out", "c2", "10:02"), ("in", "c3", "10:03"),
               ("out", "c4", "10:03"), ("in", "c5", "10:04"), ("out", "c6", "10:04")]
    chat_msgs = "".join(
        f'<div class="msg msg--{"me" if side == "in" else "them"}"><p data-i18n="{k}">{T(k)}</p>'
        f'<time>{tm}{"<i>✓✓</i>" if side == "in" else ""}</time></div>'
        for side, k, tm in bubbles
    )
    chat_section = f"""<section class="section section--grey" id="chat">
  <div class="wrap wrap--narrow">
    {el("h2", "chatTitle", "h2")}
    <div class="chat">
      <div class="chat__head"><span class="chat__ava">{ICONS["phone"]}</span>
        <div><b data-i18n="chatManager">{T("chatManager")}</b><small><i class="dot"></i><span data-i18n="chatOnline">{T("chatOnline")}</span></small></div></div>
      <p class="chat__label" data-i18n="chatLabel">{T("chatLabel")}</p>
      <div class="chat__body">{chat_msgs}</div>
    </div>
    <div class="center">{call_btn("chatCta", "chat")}</div>
  </div>
</section>"""

    # --- отзывы (только реальные, из REVIEWS)
    reviews_section = ""
    if REVIEWS:
        items = []
        for i, r in enumerate(REVIEWS):
            reg(f"rv{i}", (r["ru"], r["uz"]))
            items.append(
                f'<div class="chat review"><div class="chat__head"><span class="chat__ava chat__ava--txt">{html.escape(r["name"][:1])}</span>'
                f'<div><b>{html.escape(r["name"])}</b><small>{html.escape(r.get("model", ""))}</small></div></div>'
                f'<div class="chat__body"><div class="msg msg--them"><p data-i18n="rv{i}">{html.escape(r["ru"])}</p>'
                f'<time>{html.escape(r.get("time", ""))}</time></div></div></div>'
            )
        reviews_section = (f'<section class="section" id="reviews"><div class="wrap">{el("h2", "reviewsTitle", "h2")}'
                           f'<div class="reviews">{"".join(items)}</div></div></section>')

    faq = "".join(
        f'<details class="faq__item"><summary data-i18n="q{i}">{T(f"q{i}")}</summary>'
        f'<p data-i18n="a{i}">{T(f"a{i}")}</p></details>' for i in range(1, 7)
    )

    # --- данные калькулятора
    calc_data = {
        "model": m["name"].replace("DM-i", "<span class='nw'>DM-i</span>"),
        "terms": TERMS,
        "downs": DOWNS,
        "trims": [{k: t[k] for k in ("id", "name", "price", "rates", "banks")} for t in m["trims"]],
    }

    # --- SEO
    url = SITE["url"]
    head_links = ""
    if url:
        page_url = f"{url}/{slug}/"
        head_links = (
            f'<link rel="canonical" href="{page_url}">\n'
            f'<link rel="alternate" hreflang="ru" href="{page_url}">\n'
            f'<link rel="alternate" hreflang="uz" href="{page_url}?lang=uz">\n'
            f'<link rel="alternate" hreflang="x-default" href="{page_url}">\n'
            f'<meta property="og:url" content="{page_url}">\n'
        )
    og_img = f"{url}/assets/img/og/{slug}.jpg" if url else f"../assets/img/og/{slug}.jpg"

    ld = [
        {
            "@context": "https://schema.org",
            "@type": "AutoDealer",
            "name": "BYD Megawatt",
            "description": "Официальный дилер BYD в Ташкенте",
            "telephone": SITE["phone"],
            "url": url or None,
            "logo": f"{url}/assets/img/brand/logo-red.png" if url else None,
            "areaServed": "Tashkent",
            "department": [
                {"@type": "AutoDealer", "name": n, "telephone": SITE["phone"],
                 "address": {"@type": "PostalAddress", "streetAddress": ru,
                             "addressLocality": "Ташкент", "addressCountry": "UZ"}}
                for n, ru, _ in ADDRESSES
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "Car",
            "name": m["name"],
            "brand": {"@type": "Brand", "name": "BYD"},
            "image": og_img,
            "offers": [
                {"@type": "Offer", "name": f'{m["name"]} {t["name"]}', "price": t["price"],
                 "priceCurrency": "UZS", "availability": "https://schema.org/InStock",
                 "seller": {"@type": "AutoDealer", "name": "BYD Megawatt"}}
                for t in m["trims"]
            ],
        },
    ]
    for obj in ld:
        for k in [k for k, v in obj.items() if v is None]:
            del obj[k]

    i18n = {"ru": dict_ru, "uz": dict_uz}

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title data-i18n="metaTitle">{T("metaTitle")}</title>
<meta name="description" data-i18n-content="metaDesc" content="{html.escape(T("metaDesc"))}">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="{SITE["theme_color"]}">
<meta name="format-detection" content="telephone=no">
{head_links}<meta property="og:type" content="website">
<meta property="og:site_name" content="BYD Megawatt">
<meta property="og:locale" content="ru_RU">
<meta property="og:locale:alternate" content="uz_UZ">
<meta property="og:title" data-i18n-content="metaTitle" content="{html.escape(T("metaTitle"))}">
<meta property="og:description" data-i18n-content="metaDesc" content="{html.escape(T("metaDesc"))}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" data-i18n-content="metaTitle" content="{html.escape(T("metaTitle"))}">
<meta name="twitter:description" data-i18n-content="metaDesc" content="{html.escape(T("metaDesc"))}">
<meta name="twitter:image" content="{og_img}">
<link rel="icon" href="../assets/img/brand/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="../assets/img/brand/apple-touch-icon.png">
<link rel="preload" as="image" href="../assets/img/{slug}/{m["hero_img"]}-1200.webp" imagesrcset="{srcset(m["hero_img"])}" imagesizes="(min-width: 900px) 55vw, 100vw">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<link rel="preload" href="../assets/fonts/conthrax-hv.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../assets/css/style.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script>window.SITE={json.dumps({k: SITE[k] for k in ("phone", "gtm_id", "ga4_id", "fb_pixel_id", "ym_id")})};window.MODEL={json.dumps(slug)};</script>
<script src="../assets/js/analytics.js"></script>
</head>
<body>
<header class="top">
  <div class="wrap top__in">
    <a class="top__home" href="{SITE["main_site"]}" target="_blank" rel="noopener" data-site="header"><img class="top__logo" src="../assets/img/brand/logo-white.png" width="705" height="49" alt="BYD Megawatt"></a>
    <div class="top__right">
      <div class="lang" role="group" aria-label="Язык / Til">
        <button type="button" data-lang="ru" aria-pressed="true">RU</button>
        <button type="button" data-lang="uz" aria-pressed="false">UZ</button>
      </div>
      <a class="top__call" href="{tel}" data-call="header">{ICONS["phone"]}<span>{SITE["phone_display"]}</span></a>
    </div>
  </div>
</header>

<main>
<section class="hero">
  <div class="hero__media">{picture(m["hero_img"], m["name"], "hero__img", eager=True, sizes="(min-width: 900px) 55vw, 100vw")}</div>
  <div class="wrap hero__in">
    <div class="hero__text">
      <p class="chips"><span class="chip chip--red" data-i18n="promo">{T("promo")}</span><span class="chip" data-i18n="dealer">{T("dealer")}</span></p>
      <h1 class="hero__title" data-i18n="heroTitle">{T("heroTitle")}</h1>
      <p class="hero__sub" data-i18n="heroSub">{T("heroSub")}</p>
      <div class="hero__price">
        <span class="hero__price-label" data-i18n="payFrom">{T("payFrom")}</span>
        <strong><span data-hero-pay>{fmt(min_pay)}</span><sup>*</sup></strong>
        <span data-i18n="perMonth">{T("perMonth")}</span>
      </div>
      {call_btn("heroCta", "hero", "btn btn--red btn--xl")}
      <p class="hero__note"><i class="dot"></i><span data-i18n="heroNote">{T("heroNote")}</span></p>
      <p class="hero__foot" data-i18n="heroFoot">{T("heroFoot")}</p>
    </div>
  </div>
</section>

<section class="benefits" aria-label="Преимущества">
  <div class="wrap">
    <ul class="benefits__list">
      <li>{ICONS["percent"]}<div><b data-i18n="b1t">{T("b1t")}</b><span data-i18n="b1d">{T("b1d")}</span></div></li>
      <li>{ICONS["calendar"]}<div><b data-i18n="b2t">{T("b2t")}</b><span data-i18n="b2d">{T("b2d")}</span></div></li>
      <li>{ICONS["wallet"]}<div><b data-i18n="b3t">{T("b3t")}</b><span data-i18n="b3d">{T("b3d")}</span></div></li>
      <li>{ICONS["badge"]}<div><b data-i18n="b4t">{T("b4t")}</b><span data-i18n="b4d">{T("b4d")}</span></div></li>
    </ul>
  </div>
</section>

<section class="section section--grey" id="calc">
  <div class="wrap">
    {el("h2", "calcTitle", "h2")}
    {el("p", "calcLead", "lead")}
    <div class="calc" data-calc>
      <script type="application/json" data-calc-data>{json.dumps(calc_data)}</script>
      <div class="calc__tabs" role="tablist">
        <button type="button" role="tab" data-mode="inst" aria-selected="true"><span data-i18n="tabInst">{T("tabInst")}</span></button>
        <button type="button" role="tab" data-mode="credit" aria-selected="false"><span data-i18n="tabCredit">{T("tabCredit")}</span></button>
      </div>
      <div class="calc__body">
        <div class="calc__inputs">
          <fieldset class="calc__group"><legend data-i18n="trim">{T("trim")}</legend><div class="seg seg--trim" data-trims></div></fieldset>
          <fieldset class="calc__group"><legend data-i18n="down">{T("down")}</legend><div class="seg" data-downs></div></fieldset>
          <fieldset class="calc__group"><legend data-i18n="term">{T("term")}</legend><div class="seg seg--terms" data-terms></div></fieldset>
          <p class="calc__hint" data-hint></p>
        </div>
        <div class="calc__result">
          <p class="calc__label" data-i18n="monthly">{T("monthly")}</p>
          <p class="calc__pay"><strong data-out="pay">—</strong> <span data-i18n="perMonth">{T("perMonth")}</span></p>
          <p class="calc__badge" data-out="badge"></p>
          <dl class="calc__dl">
            <div><dt data-i18n="downSum">{T("downSum")}</dt><dd data-out="down"></dd></div>
            <div><dt data-i18n="loanSum">{T("loanSum")}</dt><dd data-out="loan"></dd></div>
            <div data-credit-only hidden><dt data-i18n="rate">{T("rate")}</dt><dd data-out="rate"></dd></div>
            <div data-credit-only hidden><dt data-i18n="overpay">{T("overpay")}</dt><dd data-out="over"></dd></div>
            <div><dt data-i18n="banks">{T("banks")}</dt><dd data-out="banks"></dd></div>
          </dl>
          {call_btn("calcCta", "calc", "btn btn--red btn--block")}
          <p class="calc__note" data-i18n="calcNote">{T("calcNote")}</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="features">
  <div class="wrap">
    {el("h2", "featTitle", "h2")}
    <ul class="feats">{feats}</ul>
  </div>
  <ul class="gallery" aria-label="Фото">{gallery}</ul>
  <div class="wrap center">{call_btn("testDrive", "testdrive", "btn btn--dark")}</div>
</section>

<section class="section section--grey" id="compare">
  <div class="wrap">
    {el("h2", "compareTitle", "h2")}
    <div class="compare-wrap">{compare_html}</div>
  </div>
</section>

{video_section}

<section class="section section--dark" id="why">
  <div class="wrap">
    {el("h2", "whyTitle", "h2")}
    <ul class="why">
      <li>{ICONS["badge"]}<b data-i18n="w1t">{T("w1t")}</b><span data-i18n="w1d">{T("w1d")}</span></li>
      <li>{ICONS["shield"]}<b data-i18n="w2t">{T("w2t")}</b><span data-i18n="w2d">{T("w2d")}</span></li>
      <li>{ICONS["bank"]}<b data-i18n="w3t">{T("w3t")}</b><span data-i18n="w3d">{T("w3d")}</span></li>
      <li>{ICONS["pin"]}<b data-i18n="w4t">{T("w4t")}</b><span data-i18n="w4d">{T("w4d")}</span></li>
    </ul>
  </div>
</section>

{chat_section}
{reviews_section}
<section class="section" id="steps">
  <div class="wrap">
    {el("h2", "stepsTitle", "h2")}
    <ol class="steps">
      <li><b data-i18n="s1t">{T("s1t")}</b><span data-i18n="s1d">{T("s1d")}</span></li>
      <li><b data-i18n="s2t">{T("s2t")}</b><span data-i18n="s2d">{T("s2d")}</span></li>
      <li><b data-i18n="s3t">{T("s3t")}</b><span data-i18n="s3d">{T("s3d")}</span></li>
    </ol>
    <div class="center">{call_btn("call", "steps")}</div>
  </div>
</section>

<section class="section section--grey" id="faq">
  <div class="wrap wrap--narrow">
    {el("h2", "faqTitle", "h2")}
    <div class="faq">{faq}</div>
  </div>
</section>

<section class="final">
  <div class="wrap final__in">
    {el("h2", "finalTitle", "h2")}
    {el("p", "finalText", "lead")}
    {call_btn("call", "final", "btn btn--white btn--xl")}
    <a class="final__phone" href="{tel}" data-call="final-phone">{SITE["phone_display"]}</a>
  </div>
</section>
</main>

<footer class="foot">
  <div class="wrap">
    <a href="{SITE["main_site"]}" target="_blank" rel="noopener" data-site="footer"><img class="foot__logo" src="../assets/img/brand/logo-white.png" width="705" height="49" alt="BYD Megawatt" loading="lazy"></a>
    {el("h2", "addrTitle", "foot__h")}
    <ul class="addr">{"".join(addr_items)}</ul>
    <p class="foot__phone"><a href="{tel}" data-call="footer">{SITE["phone_display"]}</a></p>
    <p class="foot__legal" data-i18n="legal">{T("legal")}</p>
    <p class="foot__copy">© BYD Megawatt</p>
  </div>
</footer>

<div class="sticky">{call_btn("callShort", "sticky", "btn btn--red btn--block")}</div>

<script type="application/json" id="i18n">{json.dumps(i18n, ensure_ascii=False)}</script>
<script src="../assets/js/app.js" defer></script>
</body>
</html>
"""


def index_page():
    cards = []
    for slug, m in MODELS.items():
        cards.append(
            f'<a class="pick" href="{slug}/">'
            f'<img src="assets/img/{slug}/{m["hero_img"]}-800.webp" width="800" height="600" alt="{m["name"]}" loading="lazy">'
            f'<span class="pick__name">{m["name"]}</span>'
            f'<span class="pick__offer">0% · {max_zero_term(m)} мес · от {fmt(min_installment(m))} сум/мес</span></a>'
        )
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BYD Megawatt — рассрочка 0% на BYD</title>
<meta name="description" content="Официальный дилер BYD в Ташкенте. Рассрочка 0% на BYD Chazor и Song Plus DM-i. Звоните: {SITE["phone_display"]}.">
<meta name="theme-color" content="{SITE["theme_color"]}">
<meta name="format-detection" content="telephone=no">
<link rel="icon" href="assets/img/brand/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="index">
<header class="top"><div class="wrap top__in"><a class="top__home" href="{SITE["main_site"]}" target="_blank" rel="noopener"><img class="top__logo" src="assets/img/brand/logo-white.png" width="705" height="49" alt="BYD Megawatt"></a>
<a class="top__call" href="tel:{SITE["phone"]}">{ICONS["phone"]}<span>{SITE["phone_display"]}</span></a></div></header>
<main class="section"><div class="wrap"><h1 class="h2">Рассрочка 0% на BYD</h1><div class="picks">{"".join(cards)}</div></div></main>
</body>
</html>
"""


def tilda_block(full):
    """Код для HTML-блока T123 в Тильде: ресурсы из <head> + содержимое <body>.
    Пути ../assets/ заменяются на CDN; title, meta и og задаются в настройках страницы Тильды."""
    head = full[full.index('<link rel="preconnect"'):full.index("</head>")]
    body = full[full.index("<body>") + len("<body>"):full.index("</body>")]
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\n', "", head)  # Schema.org со ссылками на старый домен не нужен
    code = (head + body).replace("../assets/", SITE["cdn"] + "/assets/")
    return f"<!-- BYD Megawatt: лендинг для блока T123. Собрано tools/build.py — вручную не править. -->\n{code.strip()}\n"


def main():
    if "--cdn" in sys.argv:  # для локальной проверки: python tools/build.py --cdn http://localhost:8000
        SITE["cdn"] = sys.argv[sys.argv.index("--cdn") + 1].rstrip("/")
    for slug in MODELS:
        full = page(slug)
        out = ROOT / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full, encoding="utf-8", newline="\n")
        print("written", out.relative_to(ROOT))
        out = ROOT / "tilda" / f"{slug}.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(tilda_block(full), encoding="utf-8", newline="\n")
        print("written", out.relative_to(ROOT))
    (ROOT / "index.html").write_text(index_page(), encoding="utf-8", newline="\n")
    print("written index.html")


if __name__ == "__main__":
    main()
