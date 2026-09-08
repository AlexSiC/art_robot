# `png2svg`

Рабочая реализация спецификации «PNG → очищенный SVG» для проекта
«Линия индустрии».

Утилита превращает темные штрихи на светлом растровом изображении в центральные
линии и создает SVG профиля `SVG-DRAW-1`.

## Быстрый запуск

Из корня проекта без установки:

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
`manifest.json`. Флаг `--debug` добавляет `skeleton.png`, а `--dry-run` не
публикует `clean.svg`.

Каталог `--out` должен отсутствовать или быть пустым: это защищает от смешения
артефактов разных заданий.

## Проверка

```bash
make test
make check
```

Реализация не загружает файлы в робот и не знает параметров FANUC. Ее
единственный интеграционный результат — `clean.svg`.

