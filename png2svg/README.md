# `png2svg`

Рабочая реализация спецификации «PNG → очищенный SVG» для проекта
«Линия индустрии».

Утилита превращает темные штрихи на светлом растровом изображении в центральные
линии и создает SVG профиля `SVG-DRAW-1`.

## Быстрый запуск

Из каталога `png2svg/` без установки:

```bash
PYTHONPATH=src python3 -m png2svg generate input.png \
  --profile profiles/raster_default_v1.yaml \
  --out build/job_001
```

Установка CLI в виртуальное окружение:

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/png2svg generate input.png \
  --profile profiles/raster_default_v1.yaml \
  --out build/job_001
```

Основные результаты: `clean.svg`, `preview.svg`, `stats.json` и
`manifest.json`. Флаг `--debug` добавляет `skeleton.png`. Режим `--dry-run`
публикует только `preview.svg` и `stats.json`.

Каталог `--out` должен отсутствовать или быть пустым: это защищает от смешения
артефактов разных заданий. Готовый каталог публикуется атомарно.

## Что реализовано

Конвейер выполняет grayscale/альфа-композитинг, апскейл, Otsu или
адаптивную бинаризацию, фильтр компонент и closing. Затем идут
Zhang–Suen-скелетизация, сборка графа, слияние близких узлов, обрезка
шпор, удаление коллинеарных микроточек, Douglas–Peucker, слияние штрихов
и детерминированная nearest-neighbor + 2-opt сортировка. Реализация не
требует `sknw` и `vpype`; их детерминированные операции реализованы внутри
пакета. Если установлен `scikit-image`, его `skeletonize` используется
автоматически; без него работает встроенный Zhang–Suen.

Движок `autotrace` и модуль заливок/штриховки остаются опциональными этапами:
базовый MVP со штриховой графикой работает через `--engine skeleton`.

## Основные флаги

- `--simplify N` — допуск в единицах `viewBox`.
- `--simplify-mm N --canvas-hint WxH` — допуск в миллиметрах.
- `--adaptive`, `--bridge-gap N`, `--smooth N` — коррекция предобработки.
- `--strict` — считать любой warning ошибкой.
- `--verify-with-svg2fanuc --svg2fanuc-profile cell.yaml` — прогнать
  `clean.svg` через установленый `svg2fanuc inspect` до публикации.

## Проверка

```bash
make test
make check
```

Реализация не загружает файлы в робот и не знает параметров FANUC. Ее
единственный интеграционный результат — `clean.svg`.
