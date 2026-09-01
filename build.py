# -*- coding: utf-8 -*-
"""
Static site generator for nika-sur-ma.github.io

All copy lives in this file. Run `python build.py` to regenerate
index.html, about.html and work/*.html. No dependencies.
"""

import hashlib
import io
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://nika-sur-ma.github.io"
NAME = "nika sür-mä"

# Change this line and rebuild to publish a contact address.
EMAIL = ""            # e.g. "hello@example.com"
TELEGRAM = ""         # e.g. "https://t.me/username"
INSTAGRAM = "https://www.instagram.com/nika_sur_ma/"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def asset(path):
    """Stamp a stylesheet or script with a content hash so an edit is never
    served from a stale cache."""
    try:
        with open(os.path.join(ROOT, path), "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()[:8]
    except OSError:
        return path
    return "%s?v=%s" % (path, h)


def t(en, ru, tag="span", cls=None):
    """A fragment that exists in both languages; CSS reveals one."""
    c = ' class="%s"' % cls if cls else ""
    return ('<{0}{1} data-t="en">{2}</{0}><{0}{1} data-t="ru">{3}</{0}>'
            .format(tag, c, en, ru))


# Cutouts are pinned at fixed angles rather than random ones so the page
# looks the same on every build.
TILTS = [-3.4, 2.6, -1.9, 3.9, -2.8, 1.7, -4.2, 2.2, -1.4, 3.1, -2.6, 1.2]


def cut(i, src, prefix, fit="cover", eager=False, klass="", flip=False):
    """One scissor-cut photograph. `flip` hangs it upside down."""
    return ('<div class="cut{k}" data-fit="{fit}" data-shape="{shape}"{flip} '
            'style="--tilt:{tilt}deg;--d:{delay}ms">'
            '<img src="{p}assets/img/{src}" alt=""{load} decoding="async">'
            '</div>').format(
        k=(" " + klass) if klass else "",
        fit=fit, shape=(i % 5) + 1, tilt=TILTS[i % len(TILTS)],
        flip=' data-flip="1"' if flip else "",
        delay=(i % 6) * 70, p=prefix, src=src,
        load=' fetchpriority="high"' if eager else ' loading="lazy"')


def bg_sources(bg, prefix):
    """Only offer the encodings that actually exist, smallest first — VP9
    does not always beat H.264, and a missing <source> costs a round trip."""
    found = []
    for ext, mime in (("webm", "video/webm"), ("mp4", "video/mp4")):
        path = os.path.join(ROOT, "assets", "video", "%s.%s" % (bg, ext))
        if os.path.exists(path):
            found.append((os.path.getsize(path), ext, mime))
    found.sort()
    return "".join('  <source src="%sassets/video/%s.%s" type="%s">\n'
                   % (prefix, bg, ext, mime) for _, ext, mime in found)


def head(title, desc, prefix, og_image, bg="portrait", grain=0):
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:image" content="{site}/assets/img/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}{css}">
<script>document.documentElement.classList.add('js')</script>
<script src="{p}{bgjs}" defer></script>
</head>
<body{body_class}>
<video id="bgv" aria-hidden="true" tabindex="-1" autoplay muted loop playsinline
       preload="auto" data-grain="{grain}" poster="{p}assets/video/{bg}-poster.jpg">
{sources}</video>
<canvas id="bg" aria-hidden="true"></canvas>
<div id="veil" aria-hidden="true"></div>
""".format(title=title, desc=desc, p=prefix, site=SITE_URL, og=og_image, bg=bg,
           grain=grain, sources=bg_sources(bg, prefix),
           css=asset("assets/css/site.css"), bgjs=asset("assets/js/bg.js"),
           body_class="{BODY_CLASS}")


def header(prefix, here=""):
    def cur(page):
        return ' aria-current="page"' if page == here else ""
    return """<header class="hdr">
  <a class="mark" href="{p}index.html">{name}</a>
  <nav class="nav">
    <a href="{p}index.html"{c1}>{work}</a>
    <a href="{p}about.html"{c2}>{about}</a>
    <div class="lang">
      <button type="button" data-lang="en" aria-pressed="true">EN</button>
      <button type="button" data-lang="ru" aria-pressed="false">RU</button>
    </div>
  </nav>
</header>
""".format(p=prefix, name=NAME,
           work=t("work", "работы"),
           about=t("about", "обо мне"),
           c1=cur("work"), c2=cur("about"))


def footer(prefix):
    links = []
    if EMAIL:
        links.append('<a href="mailto:%s">%s</a>' % (EMAIL, EMAIL))
    if TELEGRAM:
        links.append('<a href="%s" rel="me noopener">telegram</a>' % TELEGRAM)
    right = " &nbsp;/&nbsp; ".join(links) if links else t(
        "contact — to be added", "контакты — добавить")
    return """<div class="foot">
  <span>{name} &copy; 2026</span>
  <span>{right}</span>
</div>
""".format(name=NAME, right=right)


# --------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------

WORKS = [
{
 "slug": "city-15741",
 "kicker_en": "Fulldome film", "kicker_ru": "Купольный фильм",
 "title_en": "City 15741", "title_ru": "Город 15741",
 "sub_en": "Winner of the «City of the Future» dome projection competition at ДЕЛЬТА’n. "
           "A city kept in working order for no one. With Mike Iv and Pavel Gordeev.",
 "sub_ru": "Победитель конкурса купольных проекций «Город будущего» фестиваля ДЕЛЬТА’n. "
           "Город, который поддерживается в порядке ни для кого. С Майком Ивом и Павлом Гордеевым.",
 "cover": "city-04.webp", "fit": "contain",
 "meta": [
   ("Year", "Год", "2026", "2026"),
   ("Award", "Награда",
    "Winner — «City of the Future» dome projection competition",
    "Победитель конкурса купольных проекций «Город будущего»"),
   ("Festival", "Фестиваль",
    '<a href="https://delta-n-fest.com/" rel="noopener">ДЕЛЬТА’n</a> — festival-laboratory of creative synthesis, St. Petersburg',
    '<a href="https://delta-n-fest.com/" rel="noopener">ДЕЛЬТА’n</a> — фестиваль-лаборатория творческого синтеза, Санкт-Петербург'),
   ("Screening", "Показ",
    "8 September 2026, Planetarium No. 1, St. Petersburg",
    "8 сентября 2026, Планетарий №1, Санкт-Петербург"),
   ("Format", "Формат",
    "Fulldome, fisheye 180°, 4096×4096, 30 fps",
    "Фулдоум, fisheye 180°, 4096×4096, 30 к/с"),
   ("Duration", "Хронометраж", "4 min", "4 мин"),
   ("Authors", "Авторы",
    "nika sür-mä, Mike Iv, Pavel Gordeev",
    "Ника Сурма, Майк Ив, Павел Гордеев"),
 ],
 "body_en": [
   "What happens to a city if its principal function changes? The first cities arose from people’s "
   "need to come together, to exchange knowledge and to make what is impossible alone. If a human "
   "being stops being the condition on which a city exists, does its infrastructure change — does it "
   "remain at all? The city of the future may be the first one built by people and no longer "
   "dependent on them.",
   "City 15741 has no narrative. There are no people in it, no traces of people, and no moment "
   "at which they left. The city is shown afterwards — but “afterwards” is not offered as loss, "
   "because there is nothing to lose: the space does not remember what came before.",
   "Its three acts are not exposition, development and finale but three degrees of liminality. "
   "<strong>Threshold</strong> — the image still resembles a place: there is sky, a horizon and a bottom, "
   "everything is in working order, and nothing begins. <strong>Repeat</strong> — the city recurs; a loop "
   "without an original. <strong>Without scale</strong> — every point of reference disappears, including the city itself.",
   "The cold here is not temperature but working order. Nothing is ruined, nothing is abandoned, "
   "there is no dust and no wear — the city is being maintained. That is what makes it inhuman: "
   "it is kept in order for no one.",
   "On the dome the geometry of the city coincides with the geometry of the projection: the arcs "
   "of the overpasses fall as circles, the horizon closes into a full ring overhead. Haze is the only "
   "carrier of depth, so depth can be taken away by the same means. Nothing moves except the camera — "
   "a moving object would be an event, and there are no events.",
 ],
 "body_ru": [
   "Что произойдёт с городом, если его основная функция изменится? Первые города возникли "
   "из потребности людей объединяться, обмениваться знаниями и создавать то, что невозможно "
   "в одиночку. Если человек перестанет быть главным условием существования города, изменятся "
   "ли его инфраструктура, останется ли она? Город будущего может стать первым созданным "
   "человеком, но больше не зависящим от него.",
   "В фильме нет повествования. Нет людей, нет их следов, нет момента, когда они ушли. "
   "Город показан уже после — но «после» не подаётся как утрата, потому что нечего терять: "
   "пространство не помнит, что было до.",
   "Три акта — не завязка, развитие и финал, а три степени лиминальности. "
   "<strong>Порог</strong> — ещё похоже на место: есть небо, горизонт и низ, всё исправно и ничего не начинается. "
   "<strong>Повтор</strong> — город повторяется: петля без оригинала. "
   "<strong>Без масштаба</strong> — исчезает любая точка отсчёта, включая сам город.",
   "Холод здесь не в температуре, а в исправности. Ничего не разрушено, ничего не заброшено, "
   "нет пыли и следов износа — город обслуживается. Именно это делает его нечеловеческим: "
   "он поддерживается в порядке ни для кого.",
   "На куполе геометрия города совпадает с геометрией проекции: дуги эстакад ложатся "
   "окружностями, горизонт замыкается кольцом над головой. Дымка — единственный носитель глубины, "
   "значит ею же глубину можно и отнять. Ничего не движется, кроме камеры: движение объекта "
   "было бы событием, а событий здесь нет.",
 ],
 "gallery": [
   ("city-01.webp", "contain", "Act I — Threshold", "Акт I — Порог"),
   ("city-02.webp", "contain", "Act I — Threshold", "Акт I — Порог"),
   ("city-03.webp", "contain", "Act II — Repeat", "Акт II — Повтор"),
   ("city-05.webp", "contain", "Act II — Repeat", "Акт II — Повтор"),
   ("city-06.webp", "contain", "Act II — Repeat", "Акт II — Повтор"),
   ("city-07.webp", "contain", "Act II — Repeat", "Акт II — Повтор"),
   ("city-08.webp", "contain", "Act III — Without scale", "Акт III — Без масштаба"),
   ("city-09.webp", "contain", "Act III — Without scale", "Акт III — Без масштаба"),
   ("city-10.webp", "contain", "Act III — Without scale", "Акт III — Без масштаба"),
   ("city-11.webp", "contain", "Act III — Without scale", "Акт III — Без масштаба"),
 ],
},
{
 "slug": "synesthetic-rain",
 "kicker_en": "Projection mapping", "kicker_ru": "Видеомэппинг",
 "title_en": "synesthetic r(AI)n", "title_ru": "synesthetic r(AI)n",
 "sub_en": "Winner of the open call for 3D mapping on the façade of the Alexandrinsky Theatre. "
           "Digital Rain Festival, St. Petersburg, 2025.",
 "sub_ru": "Победитель опен-колла на 3D-мэппинг фасада Александринского театра. "
           "Фестиваль медиаискусства D/G/TAL RA/N, Санкт-Петербург, 2025.",
 "cover": "rain-facade.jpg", "fit": "cover", "bg": "rain",
 "hero": "rain-festival-poster.jpg",
 "meta": [
   ("Year", "Год", "2025", "2025"),
   ("Award", "Награда",
    "Winner of the open call for 3D mapping on the façade of the Alexandrinsky Theatre",
    "Победитель опен-колла на 3D-мэппинг фасада Александринского театра"),
   ("Festival", "Фестиваль",
    "D/G/TAL RA/N — Festival of Media Art, St. Petersburg, 25–28 September 2025",
    "D/G/TAL RA/N — фестиваль медиаискусства, Санкт-Петербург, 25–28 сентября 2025"),
   ("Site", "Площадка",
    "Façade of the Alexandrinsky Theatre",
    "Фасад Александринского театра"),
 ],
 "body_en": [
   "A fantasy on the theme of synesthetic flow, inspired by two paintings of Wassily "
   "Kandinsky: <em>Composition VI</em> and <em>Composition VII</em>.",
   "At its centre is the idea of the Flood — not as a story but as an inner state: renewal "
   "through destruction, the equilibrium of opposites, the dissolution of the image into pure "
   "painting. On the façade this becomes an endless synthetic rain, a symbol of perpetual flow "
   "in which catastrophe and restoration exist at the same time, and art becomes a space of "
   "continuous rebirth.",
 ],
 "body_ru": [
   "Фантазия на тему синестетического потока, вдохновлённая работами Василия Кандинского: "
   "«Композиция VI» и «Композиция VII».",
   "В центре — идея Всемирного потопа не как сюжета, а как внутреннего состояния: обновление "
   "через разрушение, равновесие противоположностей, растворение образа в чистой живописи. "
   "В мэппинге это превращается в бесконечный синтетический дождь — символ вечного потока, "
   "где катастрофа и восстановление существуют одновременно, а искусство становится "
   "пространством непрерывного перерождения.",
 ],
 "gallery": [],
},
{
 "slug": "magic-lantern",
 "kicker_en": "Interactive theatre game", "kicker_ru": "Интерактивная театральная игра",
 "title_en": "Magic Lantern", "title_ru": "Волшебный фонарь",
 "sub_en": "Night of Light, Gatchina, 2025. Media art and sound design; music and animation.",
 "sub_ru": "«Ночь света», Гатчина, 2025. Медиахудожница и саунд-дизайн; музыка и анимация.",
 "cover": "lantern-credits.jpg", "fit": "contain", "bg": "lantern", "flip": True,
 "meta": [
   ("Year", "Год", "2025", "2025"),
   ("Festival", "Фестиваль",
    "Night of Light, Gatchina Museum-Reserve",
    "«Ночь света», Гатчинский музей-заповедник"),
   ("Role", "Роль",
    "Media artist, sound design — music and animation",
    "Медиахудожница, саунд-дизайн — музыка и анимация"),
   ("Team", "Команда",
    "Mikhail Patlasov (director), Mike Iv, nika sür-mä, Angelina Lakeeva, "
    "Alina Shklyarskaya (text), Egor Shcherbak",
    "Михаил Патласов (режиссёр), Mike Iv, nika sür-mä, Ангелина Лакеева, "
    "Алина Шклярская (текст), Егор Щербак"),
   ("Support", "Поддержка",
    "New Media Laboratory (Meyerhold New Stage, Alexandrinsky Theatre); "
    "technical support — Gobo Image",
    "Лаборатория новых медиа (Новая сцена им. Вс. Мейерхольда, Александринский театр); "
    "техническая поддержка — Gobo Image"),
 ],
 "body_en": [
   "Emperor Alexander III considered Gatchina his home, and every hall here holds memories of "
   "work, play, love and hospitality. One of the imperial family’s domestic entertainments in the "
   "nineteenth century was the viewing of stereoscopic images: with the help of a magic lantern one "
   "could travel to distant countries or recall a family journey. The stereoscope can be considered "
   "a prototype of the projector.",
   "The dialogue between the emperor and the audience — impossible, and nevertheless taking place "
   "here and now — is built on the juxtaposition of authentic and contemporary technology, of the "
   "contemporary and the historical order of palace life.",
   "Every fifteen minutes an interactive session takes place in the Arsenal Square. Visitors enter "
   "into communication with the former inhabitants of the Gatchina Palace and tell them about themselves.",
 ],
 "body_ru": [
   "Император Александр III считал Гатчину своим домом, и каждый зал здесь хранит "
   "воспоминания о работе, игре, любви и гостеприимстве. Одним из домашних развлечений "
   "императорской семьи в XIX веке были сеансы просмотра стереоскопических изображений: "
   "с помощью «волшебного фонаря» можно было перенестись в далёкие страны или вспомнить "
   "семейные путешествия. Стереоскоп можно считать прототипом проектора.",
   "На сопоставлении аутентичной и современной технологии, современного и старинного "
   "уклада жизни дворца строится диалог императора со зрителем, невозможный, "
   "но тем не менее происходящий здесь и сейчас.",
   "Каждые 15 минут в Арсенальном каре проходят интерактивные сеансы. Зрителям "
   "предстоит вступить в коммуникацию с прошлыми обитателями Гатчинского дворца "
   "и рассказать о себе.",
 ],
 "gallery": [],
},
{
 "slug": "cage-of-dome",
 "kicker_en": "AR installation", "kicker_ru": "AR-инсталляция",
 "title_en": "The Cage of DOME", "title_ru": "The Cage of DOME",
 "sub_en": "The glitch as an autonomous presence inside a digital environment. "
           "Glitching Environments, group exhibition, AIR ITMO, 2026.",
 "sub_ru": "Глитч как автономное присутствие внутри цифровой среды. "
           "«Сбоящие среды», групповая выставка, AIR ITMO, 2026.",
 "cover": "cage-poster.jpg", "fit": "cover", "bg": "cage", "grain": 0.1,
 "meta": [
   ("Year", "Год", "2026", "2026"),
   ("Exhibition", "Выставка",
    "Glitching Environments — group exhibition, AIR, ITMO",
    "«Сбоящие среды» — групповая выставка, AIR, ИТМО"),
   ("Role", "Роль",
    "3D modelling, AR, video, sound",
    "3D-моделирование, AR, видео, звук"),
 ],
 "body_en": [
   "The project explores the glitch as an autonomous presence within a digital environment. At the "
   "centre of the installation is a translucent glitch cube that instantly registers the moment an "
   "error occurs and becomes the source of all subsequent transformations.",
   "Inside the cube are three nested spheres, each responding to the glitch with a temporal delay: "
   "the White Sphere as a primary container, the Station as a transitional state, and the Burned Place "
   "as a residue of loss and disruption. Behind and beyond these forms, rectangular echo-traces "
   "accumulate, representing unrealised or postponed states.",
   "The installation embodies John Cage’s philosophy that events simply occur: the glitch here is "
   "not a failure but a material event that generates effects, shapes space, and leaves traces. "
   "Visitors perceive the cube as the active agent, the spheres as dependent reactions, and the "
   "trailing rectangular forms as memory and temporal propagation. The visual language — glitch "
   "textures, transparency, recursive forms, echoing traces — renders the behaviour of the error "
   "tangible and perceptible.",
 ],
 "body_ru": [
   "Проект исследует глитч как автономное присутствие внутри цифровой среды. В центре "
   "инсталляции — полупрозрачный глитч-куб, который мгновенно регистрирует момент "
   "возникновения ошибки и становится источником всех последующих трансформаций.",
   "Внутри куба — три вложенные сферы, каждая отвечает на глитч с временной задержкой: "
   "Белая сфера как первичный контейнер, Станция как переходное состояние и Выжженное место "
   "как остаток потери и разрыва. За этими формами накапливаются прямоугольные эхо-следы — "
   "нереализованные или отложенные состояния.",
   "Инсталляция воплощает философию Джона Кейджа: события просто случаются. Глитч здесь — "
   "не сбой, а материальное событие, которое порождает эффекты, формирует пространство и оставляет следы. "
   "Визуальный язык — глитч-текстуры, прозрачность, рекурсивные формы и эхо-следы — "
   "делает поведение ошибки осязаемым.",
 ],
 "gallery": [],
},
{
 "slug": "addoor-error",
 "kicker_en": "Audiovisual story", "kicker_ru": "Аудиовизуальная история",
 "title_en": "ad(do)Or_e(a)Rror", "title_ru": "ad(do)Or_e(a)Rror",
 "sub_en": "Selected for the special project of PS-2025: Stories in A/V. "
           "The story of the most adorable oak-like error in the network.",
 "sub_ru": "Отобран в спец-проект ПС-2025 «Все прекрасные аудиовизуальные истории». "
           "История самой обаятельной дубоподобной ошибки в сети.",
 "cover": "ps2025-poster.jpg", "fit": "cover", "bg": "error",
 "meta": [
   ("Year", "Год", "2025", "2025"),
   ("Programme", "Программа",
    "Special project PS-2025: Stories in A/V",
    "Спец-проект ПС-2025: Все прекрасные аудио-визуальные истории"),
   ("Festival", "Фестиваль",
    "17th International Festival of Experimental Sound — Prepared Environments 2025, "
    "an informal dedication to John Cage",
    "XVII Международный фестиваль экспериментального звука «Подготовленные среды 2025», "
    "неформальное посвящение Джону Кейджу"),
   ("Tools", "Инструменты",
    "Ableton Live, TouchDesigner, MAX/MSP, Hailuo AI",
    "Ableton Live, TouchDesigner, MAX/MSP, Hailuo AI"),
 ],
 "body_en": [
   "The story of the most adorable oak-like error in the network. ad(do)Or_e(a)Rror explores a space "
   "of digital instability — a state in which an error becomes a structural, autonomous element, alive, "
   "yet its identity loses stability under the pressure of networked representations.",
   "The project combines field recordings, AI “breaths” and whispers, and objects synthesised in the "
   "MAX/MSP environment, creating a multilayered field where rupture, displacement and interruption "
   "function as new forms of meaning-making.",
 ],
 "body_ru": [
   "История самой обаятельной дубоподобной ошибки в сети. ad(do)Or_e(a)Rror исследует пространство "
   "цифровой нестабильности — состояние, в котором ошибка становится структурным, автономным "
   "элементом, живым, но её идентичность теряет устойчивость под давлением сетевых репрезентаций.",
   "Проект соединяет полевые записи, ИИ-«дыхания» и шёпоты, а также синтезированные объекты в среде "
   "MAX/MSP, создавая многослойное поле, где разрыв, смещение и прерывание работают "
   "как новые формы смыслообразования.",
 ],
 "gallery": [],
},
{
 "slug": "deconstruction-of-ai",
 "kicker_en": "8-channel audio installation", "kicker_ru": "8-канальная звуковая инсталляция",
 "title_en": "de[]construction of A(I)", "title_ru": "de[]construction of A(I)",
 "sub_en": "Graduation work, Soundartist.ru. Krasnokholmskaya Gallery, Moscow, 22.07 — 07.09.2025.",
 "sub_ru": "Дипломная работа, Soundartist.ru. Краснохолмская галерея, Москва, 22.07 — 07.09.2025.",
 "cover": "deconstruction.jpg", "fit": "cover",
 "meta": [
   ("Year", "Год", "2025", "2025"),
   ("Form", "Форма",
    "8-channel audio installation",
    "8-канальная звуковая инсталляция"),
   ("Context", "Контекст",
    "Graduation work, Soundartist.ru",
    "Дипломная работа, Soundartist.ru"),
   ("Venue", "Площадка",
    "Krasnokholmskaya Gallery, Moscow, 22.07 — 07.09.2025",
    "Краснохолмская галерея, Москва, 22.07 — 07.09.2025"),
   ("Link", "Ссылка",
    '<a href="https://kholmy.vzmoscow.ru/whispers" rel="noopener">kholmy.vzmoscow.ru/whispers</a>',
    '<a href="https://kholmy.vzmoscow.ru/whispers" rel="noopener">kholmy.vzmoscow.ru/whispers</a>'),
 ],
 "body_en": [
   "An eight-channel audio installation built as the graduation work of the Soundartist.ru programme "
   "and shown at the Krasnokholmskaya Gallery in Moscow.",
   "Eight speakers distribute the material around the room so that the listener never occupies a "
   "single fixed point of the mix: the work is de- and re-constructed differently at every position "
   "in the space.",
 ],
 "body_ru": [
   "Восьмиканальная звуковая инсталляция, сделанная как дипломная работа программы Soundartist.ru "
   "и показанная в Краснохолмской галерее в Москве.",
   "Восемь колонок распределяют материал по комнате так, что слушатель никогда не находится "
   "в единственной точке микса: работа де- и реконструируется по-разному в каждой "
   "точке пространства.",
 ],
 "gallery": [],
},
{
 "slug": "lez-acoustic-trace",
 "kicker_en": "Sound art", "kicker_ru": "Саунд-арт",
 "title_en": "LEZ: Acoustic Trace", "title_ru": "ЛЭЗ: Акустический след",
 "sub_en": "Laboratory of Experimental Sound, Dom Radio. Modular synthesis, field recording, "
           "acoustic experimental composition.",
 "sub_ru": "Лаборатория экспериментального звука, Дом радио. Модулярный синтез, "
           "полевые записи, акустическая экспериментальная композиция.",
 "cover": "lez-hall.jpg", "fit": "cover",
 "meta": [
   ("Year", "Год", "2025", "2025"),
   ("Institution", "Площадка", "Dom Radio, St. Petersburg", "Дом радио, Санкт-Петербург"),
   ("Exhibition", "Выставка",
    "Acoustic Trace, 1.10 — 21.12.2025",
    "«Акустический след», 1.10 — 21.12.2025"),
   ("Laboratories", "Лаборатории",
    "Modular Sound Synthesis; Field Recording sessions; Acoustic Experimental Composition",
    "Модулярный синтез звука; сессии полевых записей; акустическая экспериментальная композиция"),
 ],
 "body_en": [
   "Participant in the laboratories of the Laboratory of Experimental Sound at Dom Radio: "
   "Modular Sound Synthesis, Field Recording sessions, and Acoustic Experimental Composition.",
   "The work made in these labs treats recording as a trace rather than a document — what remains "
   "of a room once the sound that described it has stopped.",
 ],
 "body_ru": [
   "Участница лабораторий ЛЭЗ в Доме радио: модулярный синтез звука, сессии полевых "
   "записей, акустическая экспериментальная композиция.",
   "Запись здесь — не документ, а след: то, что остаётся от помещения, когда звук, "
   "описывавший его, прекратился.",
 ],
 "gallery": [
   ("lez-synth.jpg", "cover", "Modular synthesis lab", "Лаборатория модулярного синтеза"),
   ("lez-poster.jpg", "cover", "Acoustic Trace, 1.10 — 21.12.2025", "«Акустический след», 1.10 — 21.12.2025"),
 ],
},
{
 "slug": "ivory-tower-vii",
 "kicker_en": "Sound laboratory", "kicker_ru": "Звуковая лаборатория",
 "title_en": "Ivory Tower VII", "title_ru": "Башня из слоновой кости VII",
 "sub_en": "Sound production in sonic improvisation with experimental instruments from Dom Radio.",
 "sub_ru": "Звуковое производство в звуковой импровизации на экспериментальных инструментах Дома радио.",
 "cover": "ivory.jpg", "fit": "cover", "bg": "ivory",
 "meta": [
   ("Role", "Роль",
    "Participant in the laboratory",
    "Участница лаборатории"),
   ("Instruments", "Инструменты",
    "Experimental instruments from Dom Radio",
    "Экспериментальные инструменты Дома радио"),
   ("Documentation", "Документация",
    "Video documentation held in a private collection",
    "Видеодокументация в частной коллекции"),
 ],
 "body_en": [
   "As a participant in the laboratory, nika sür-mä explored sound production in sonic improvisation "
   "using experimental instruments from Dom Radio.",
 ],
 "body_ru": [
   "В качестве участницы лаборатории Ника Сурма исследовала звуковое производство в звуковой "
   "импровизации на экспериментальных инструментах Дома радио.",
 ],
 "gallery": [
   ("cables.jpg", "cover", "", ""),
 ],
},
]


CV = [
 ("2026", "<b>City 15741</b> — winner, «City of the Future» dome projection competition, ДЕЛЬТА’n; screening at Planetarium No. 1, St. Petersburg",
          "<b>Город 15741</b> — победитель конкурса купольных проекций «Город будущего», ДЕЛЬТА’n; показ в Планетарии №1, Санкт-Петербург"),
 ("2026", "<b>The Cage of DOME</b> — Glitching Environments, group exhibition, AIR, ITMO",
          "<b>The Cage of DOME</b> — «Сбоящие среды», групповая выставка, AIR, ИТМО"),
 ("2025", "<b>synesthetic r(AI)n</b> — winner of the open call for 3D mapping on the façade of the Alexandrinsky Theatre, D/G/TAL RA/N",
          "<b>synesthetic r(AI)n</b> — победитель опен-колла на 3D-мэппинг фасада Александринского театра, D/G/TAL RA/N"),
 ("2025", "<b>Magic Lantern</b> — interactive theatre game, Night of Light, Gatchina",
          "<b>Волшебный фонарь</b> — интерактивная театральная игра, «Ночь света», Гатчина"),
 ("2025", "<b>ad(do)Or_e(a)Rror</b> — special project, PS-2025: Stories in A/V",
          "<b>ad(do)Or_e(a)Rror</b> — спец-проект ПС-2025: Все прекрасные аудиовизуальные истории"),
 ("2025", "<b>de[]construction of A(I)</b> — 8-channel audio installation, graduation work (Soundartist.ru), Krasnokholmskaya Gallery, Moscow",
          "<b>de[]construction of A(I)</b> — 8-канальная звуковая инсталляция, диплом (Soundartist.ru), Краснохолмская галерея, Москва"),
 ("2025", "<b>Touch Me {Maybe}</b> — with Lera Juffer, AIR, ITMO",
          "<b>Touch Me {Maybe}</b> — совместно с Lera Juffer, AIR, ИТМО"),
 ("2025", "<b>LEZ: Acoustic Trace</b> — Laboratory of Experimental Sound, Dom Radio",
          "<b>ЛЭЗ: Акустический след</b> — Лаборатория экспериментального звука, Дом радио"),
 ("2025", "<b>Ivory Tower VII</b> — sound laboratory, Dom Radio",
          "<b>Башня из слоновой кости VII</b> — звуковая лаборатория, Дом радио"),
]

BIO_EN = [
 "Nika sür-mä is a media artist whose practice investigates agentic systems in media and their "
 "role in transforming human perception and agency. Working with sound, generative systems, AI, "
 "augmented reality, 3D environments, and spatial composition, she creates experimental situations "
 "in which humans interact with autonomous and semi-autonomous processes.",
 "Her work explores the emergence of the posthuman through the redistribution of agency between "
 "humans, machines, algorithms, and environments. Rather than treating technology as a tool, she "
 "approaches media systems as active participants capable of influencing perception, behavior, "
 "and artistic production.",
]

BIO_RU = [
 "Nika sür-mä — медиахудожница, чья практика исследует агентные системы в медиа и их роль "
 "в трансформации человеческого восприятия и агентности. Работая со звуком, генеративными "
 "системами, ИИ, дополненной реальностью, 3D-средами и пространственной композицией, она "
 "создаёт экспериментальные ситуации, в которых человек взаимодействует с автономными "
 "и полуавтономными процессами.",
 "Её работа исследует возникновение постчеловеческого через перераспределение агентности "
 "между людьми, машинами, алгоритмами и средами. Вместо того чтобы относиться к технологии "
 "как к инструменту, она рассматривает медиасистемы как активных участников, способных "
 "влиять на восприятие, поведение и художественное производство.",
]


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def write(path, html):
    full = os.path.join(ROOT, path)
    d = os.path.dirname(full)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("  ", path)


def render_index():
    slides = []
    dots = []
    for i, w in enumerate(WORKS):
        slides.append("""  <section class="slide" data-fit="{fit}" id="s{n}">
    <div class="cap">
      <p class="kicker">{kicker}</p>
      <h2>{title}</h2>
      <p class="sub">{sub}</p>
      <span class="go">{go}</span>
    </div>
    {cutout}
    <a class="hit" href="work/{slug}.html" aria-label="{title_en}"></a>
  </section>""".format(
            fit=w["fit"], n=i + 1, slug=w["slug"], title_en=w["title_en"],
            cutout=cut(i, w["cover"], "", w["fit"], eager=(i == 0),
                       flip=w.get("flip", False)),
            kicker=t(w["kicker_en"], w["kicker_ru"]),
            title=t(w["title_en"], w["title_ru"]),
            sub=t(w["sub_en"], w["sub_ru"]),
            go=t("view project", "смотреть проект")))
        dots.append('    <button type="button" aria-current="{cur}" '
                    'aria-label="{lab}">{num:02d}</button>'
                    .format(cur="true" if i == 0 else "false",
                            lab=w["title_en"], num=i + 1))

    html = head(
        "nika sür-mä — media artist",
        "Agentic systems in media and their role in transforming human perception and agency: "
        "fulldome film, projection mapping, AR and multichannel sound.",
        "", WORKS[0]["cover"]).replace("{BODY_CLASS}", ' class="deck-page"')
    html += header("", "work")
    html += '<main class="deck">\n' + "\n".join(slides) + "\n</main>\n"
    html += '<nav class="pager" aria-label="Projects">\n' + "\n".join(dots) + "\n</nav>\n"
    html += '<p class="hint">{}</p>\n'.format(
        t("scroll", "скролл"))
    html += ('<script src="%s" defer></script>\n</body>\n</html>\n'
             % asset("assets/js/site.js"))
    write("index.html", html)


def render_work(i, w):
    nxt = WORKS[(i + 1) % len(WORKS)]

    meta = []
    for en_l, ru_l, en_v, ru_v in w["meta"]:
        meta.append("      " + t(en_l, ru_l, "dt"))
        meta.append("      " + t(en_v, ru_v, "dd"))

    prose = []
    for p_en, p_ru in zip(w["body_en"], w["body_ru"]):
        prose.append('      <div data-t="en">%s</div>' % wrap_para(p_en))
        prose.append('      <div data-t="ru">%s</div>' % wrap_para(p_ru))

    gallery = ""
    if w["gallery"]:
        figs = []
        for j, (src, fit, cap_en, cap_ru) in enumerate(w["gallery"]):
            cap = ""
            if cap_en or cap_ru:
                cap = "\n      <figcaption>%s</figcaption>" % t(cap_en, cap_ru)
            figs.append('    <figure class="cut-item">\n      %s%s\n    </figure>'
                        % (cut(j + 1, src, "../", fit), cap))
        gallery = ('  <p class="section-label">%s</p>\n  <div class="grid">\n%s\n  </div>\n'
                   % (t("Images", "Изображения"),
                      "\n".join(figs)))

    html = head(
        "%s — %s" % (w["title_en"], NAME),
        re.sub("<[^>]+>", "", w["sub_en"]),
        "../", w["cover"],
        bg=w.get("bg", "portrait"), grain=w.get("grain", 0)).replace(
            "{BODY_CLASS}", ' class="bg-%s"' % w.get("bg", "portrait"))
    html += header("../", "work")
    html += """<main>
<section class="hero" data-fit="{fit}">
  <div class="cap">
    <p class="kicker">{kicker}</p>
    <h1>{title}</h1>
    <p class="sub">{sub}</p>
  </div>
  {cutout}
</section>

<div class="wrap">
  <div class="cols">
    <div class="meta">
      <dl>
{meta}
      </dl>
    </div>
    <div class="prose">
{prose}
    </div>
  </div>
{gallery}  <div class="next">
    <a href="{nslug}.html">
      <span class="lbl">{nextlbl}</span><br>
      <span class="ttl">{ntitle}</span>
    </a>
  </div>
{footer}</div>
</main>
<script src="../{sitejs}" defer></script>
</body>
</html>
""".format(fit=w["fit"],
           cutout=cut(i, w.get("hero", w["cover"]), "../", w["fit"], eager=True,
                      flip=w.get("flip", False)),
           kicker=t(w["kicker_en"], w["kicker_ru"]),
           title=t(w["title_en"], w["title_ru"]),
           sub=t(w["sub_en"], w["sub_ru"]),
           meta="\n".join(meta), prose="\n".join(prose), gallery=gallery,
           nslug=nxt["slug"],
           nextlbl=t("Next project", "Следующий проект"),
           ntitle=t(nxt["title_en"], nxt["title_ru"]),
           sitejs=asset('assets/js/site.js'),
           footer=footer("../"))
    write("work/%s.html" % w["slug"], html)


def wrap_para(text):
    """Body entries are either a paragraph or a raw block (e.g. a <ul>)."""
    stripped = text.strip()
    if stripped.startswith("<ul") or stripped.startswith("<ol"):
        return stripped
    return "<p>%s</p>" % stripped


def render_about():
    rows = []
    for yr, en, ru in CV:
        rows.append('    <div class="row"><span class="yr">{yr}</span>'
                    '<span class="what">{what}</span></div>'
                    .format(yr=yr, what=t(en, ru)))

    contact = []
    if EMAIL:
        contact.append('<a href="mailto:%s">%s</a>' % (EMAIL, EMAIL))
    if TELEGRAM:
        contact.append('<a href="%s" rel="me noopener">Telegram</a>' % TELEGRAM)
    contact_html = "<br>".join(contact) if contact else t(
        "Contact details to be added — set EMAIL in build.py and rebuild.",
        "Контакты будут добавлены — укажите EMAIL в build.py и пересоберите сайт.")

    html = head("About — %s" % NAME,
                re.sub("<[^>]+>", "", BIO_EN[0]),
                "", "portrait.jpg",
                bg="portrait").replace("{BODY_CLASS}", ' class="about-page"')
    html += header("", "about")
    html += """<main>
<div class="wrap about-top">
  <div class="cols">
    <div class="portrait">
      <a class="cut reel" data-shape="2" style="--tilt:-2.4deg"
         href="{instagram}" target="_blank" rel="me noopener">
        <video autoplay muted loop playsinline preload="metadata"
               poster="assets/video/reel-poster.jpg" aria-label="{alt}">
          <source src="assets/video/reel.mp4" type="video/mp4">
        </video>
        <span class="reel-tag">instagram</span>
      </a>
    </div>
    <div>
      <h1>{name}</h1>
      <div class="prose">
        <div data-t="en">{bio_en}</div>
        <div data-t="ru">{bio_ru}</div>
      </div>

      <p class="section-label">{selected}</p>
      <div class="cv">
{rows}
      </div>

      <p class="section-label">{contact_lbl}</p>
      <p class="contact">{contact}</p>
    </div>
  </div>
{footer}</div>
</main>
<script src="{sitejs}" defer></script>
</body>
</html>
""".format(alt=NAME, name=NAME, instagram=INSTAGRAM,
           bio_en="".join("<p>%s</p>" % p for p in BIO_EN),
           bio_ru="".join("<p>%s</p>" % p for p in BIO_RU),
           selected=t("Selected works", "Избранные работы"),
           rows="\n".join(rows),
           contact_lbl=t("Contact", "Контакты"),
           contact=contact_html,
           sitejs=asset('assets/js/site.js'),
           footer=footer(""))
    write("about.html", html)


def render_extras():
    write("assets/favicon.svg",
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
          '<rect width="32" height="32" fill="#0a0a0b"/>'
          '<circle cx="16" cy="16" r="11" fill="none" stroke="#eceae5" stroke-width="1.4"/>'
          '<circle cx="16" cy="16" r="4.5" fill="#eceae5"/></svg>\n')

    urls = ["", "about.html"] + ["work/%s.html" % w["slug"] for w in WORKS]
    body = "".join("  <url><loc>%s/%s</loc></url>\n" % (SITE_URL, u) for u in urls)
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + body + "</urlset>\n")

    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE_URL)
    write(".nojekyll", "")


def prune_work_pages():
    """Drop pages for works that no longer exist, so a removed project does
    not stay reachable by its old URL."""
    keep = {"%s.html" % w["slug"] for w in WORKS}
    d = os.path.join(ROOT, "work")
    if not os.path.isdir(d):
        return
    for f in os.listdir(d):
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join(d, f))
            print("   removed work/%s" % f)


if __name__ == "__main__":
    print("building %s" % SITE_URL)
    prune_work_pages()
    render_index()
    for i, w in enumerate(WORKS):
        render_work(i, w)
    render_about()
    render_extras()
    print("done — %d works" % len(WORKS))
