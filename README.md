# nika-sur-ma.github.io

Портфолио: купольное кино, видеомэппинг, AR, многоканальный звук.
Статический сайт, двуязычный (RU/EN), без зависимостей и без сборщиков.

## Что где

```
build.py              весь текст сайта + генератор страниц
index.html            слайд-дек (генерируется)
about.html            био и CV (генерируется)
work/*.html           страницы проектов (генерируются)
assets/css/site.css   стили
assets/js/site.js     дек, пагинация, переключатель языка
assets/js/bg.js       интерактивный фон (WebGL2): синий дым и жидкое смещение
assets/img/           изображения
```

**HTML-файлы редактировать не нужно** — они перезаписываются. Весь текст
живёт в `build.py`, в списках `WORKS`, `CV`, `BIO_EN`, `BIO_RU`.

## Пересобрать

```bash
python build.py
```

Ничего ставить не надо — только Python 3.

## Посмотреть локально

```bash
python -m http.server 8899
```

Затем открыть http://127.0.0.1:8899

## Добавить проект

1. Положить картинки в `assets/img/`.
2. Добавить словарь в список `WORKS` в `build.py` (проще всего скопировать
   соседний и заменить поля). `fit: "contain"` — для квадратных купольных
   кадров, `fit: "cover"` — для обычных фотографий.
3. `python build.py`.

## Контакты

В `build.py` вверху есть `EMAIL` и `TELEGRAM` — они пустые. Заполнить и
пересобрать, тогда адрес появится в подвале и на странице «обо мне».

## Фон

Фон — это рендер из TouchDesigner-патча «Smoke and Liquid Displacement
Effects» (нода `/project1/comp4`), выведенный бесшовным лупом на 12 секунд:
`assets/video/smoke.mp4` + `smoke.webm` + постер. Видео и есть картинка;
WebGL сверху ничего не рисует заново, а только смещает эти же кадры под
курсором — то самое liquid displacement, только от мыши.

Настройки в `assets/js/bg.js`: `WARP = 0` полностью выключает интерактивное
смещение и оставляет чистый луп, `STRENGTH` меняет, насколько сильно курсор
тянет изображение. Плотность фона — в `site.css`: `--bg-opacity` и
затемняющая плёнка `#veil` (на деке она слабее, на внутренних страницах
плотнее, чтобы текст читался). Без WebGL2 просто играет `<video>`, при
`prefers-reduced-motion` остаётся неподвижный постер.

### Пересобрать фон из TouchDesigner

`tools/render_background.py` разбирает `.toe` через `toeexpand`, вписывает в
него Execute DAT, который сохраняет кадры `comp4` и закрывает TouchDesigner,
и собирает обратно через `toecollapse`. Правьте вверху скрипта `SRC` (путь к
проекту) и `N_FRAMES`, затем:

```bash
python tools/render_background.py
```

Запустить получившийся `render/smoke_render.toe` в TouchDesigner — он сам
отрендерит кадры и закроется. Затем:

```bash
python tools/make_loop.py
```

Скрипт делает бесшовный луп (кроссфейд последних 2 секунд с началом) и
кодирует mp4/webm/постер прямо в `assets/video/`.

### Фон страницы «обо мне»

У `about.html` свой фон — размытый портретный клип (`assets/video/portrait.*`).
Пересобрать из другого исходника:

```bash
python tools/make_about_loop.py "путь\к\клипу.mp4"
```

Скрипт апскейлит до 1440×1440 (lanczos), размывает (`SIGMA` вверху файла) и
склеивает бумеранг — прямой проход плюс обратный, — потому что исходник
уходит от светлого к тёмному и обычный луп дал бы скачок на стыке.

Какой ролик на какой странице, задаётся в `build.py`: `head(..., bg="smoke")`
по умолчанию, `bg="portrait"` в `render_about`.

## Публикация на GitHub Pages

Репозиторий должен называться `nika-sur-ma.github.io` и лежать в аккаунте
`nika-sur-ma` — тогда сайт открывается на https://nika-sur-ma.github.io

```bash
git remote add origin https://github.com/nika-sur-ma/nika-sur-ma.github.io.git
git push -u origin main
```

Затем в настройках репозитория: Settings → Pages → Source: `Deploy from a
branch`, ветка `main`, папка `/ (root)`.
