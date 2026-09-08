# svg2fanuc

Реализация спецификации **«Спецификация — очищенный SVG в траекторию FANUC.md»**
(проект «Линия индустрии»).

Модуль превращает **очищенный SVG** (профиль `SVG-DRAW-1`) в программу FANUC
`.LS` плюс нейтральный план движений, предпросмотр, отчёт и воспроизводимый
manifest. Растровую векторизацию делает соседний модуль `png2svg` — сюда
поступает уже готовый SVG.

> **GENERATED ≠ SAFE TO RUN.** Максимальное состояние задания — `COMPILED_UNVERIFIED`.
> Физический запуск из этого CLI невозможен by design. Достижимость,
> сингулярности, коллизии и безопасность ячейки подтверждает интегратор и
> ROBOGUIDE, не эта программа.

## Установка

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

Зависимости: `svgelements`, `defusedxml`, `PyYAML` (все открытые, зафиксированы
по версиям в `pyproject.toml`).

## Использование

```bash
# Проверить вход и построить отчёт без FANUC-кода
svg2fanuc inspect  drawing.svg --profile profiles/example_cell.yaml --out build/job_001

# Создать траекторию, preview, manifest и FANUC LS
svg2fanuc generate drawing.svg --profile profiles/example_cell.yaml --out build/job_001

# Скомпилировать LS -> TP (нужен MakeTP из WinOLPC/ROBOGUIDE, compile.enabled: true)
svg2fanuc compile  build/job_001/manifest.json

# Проверить контрольные суммы ранее созданного задания
svg2fanuc verify   build/job_001/manifest.json
```

`--production` для `generate` требует полностью квалифицированный профиль (без `TBD`).
`--developer` (перед подкомандой) включает подробные логи и трейсбеки.

### Коды завершения (раздел 4.2 спецификации)

| Код | Значение |
|---:|---|
| 0 | успех |
| 2 | ошибка CLI или профиля / профиль не квалифицирован |
| 3 | невалидный / неподдерживаемый SVG |
| 4 | геометрия не проходит ограничения |
| 5 | превышен бюджет точек / программ |
| 6 | ошибка генерации LS |
| 7 | ошибка MakeTP |
| 8 | нарушена целостность manifest |
| 9 | внутренняя ошибка |

## Артефакты задания

```
job_001/
├── normalized.svg     # разрешённая геометрия с применёнными transforms
├── preview.svg        # чёрным — контакт, красным пунктиром — переходы, зелёным — старты
├── trajectory.json    # vendor-neutral Motion IR — единственный источник для эмиттеров
├── report.json        # метрики, warnings, проверки, safety_notice, job_state
├── manifest.json      # SHA-256 входа/профиля/выходов, версии, флаг production
├── ART00001.LS        # master либо единственная программа
├── A0000101.LS …      # подпрограммы при дроблении (master их CALL-ит по очереди)
└── ART00001.TP        # опционально после `compile`
```

## Архитектура

```
clean.svg + cell.yaml
  → [A] secure SVG gate           security.py
  → [B] parse + viewBox/transforms svg_reader.py
  → [C] subpaths → strokes        svg_reader.py
  → [D] scale into canvas mm      transform.py
  → [E] adaptive flattening (mm)  flatten.py
  → [F] dedupe + validate         strokes.py / geometry.py
  → [G] routing (order only)      routing.py
  → [H] clear/plunge/draw/retract motion_ir.py
  → [I] trajectory.json           motion_ir.py
  → [J] preview / report          preview.py / report.py
  → [K] FANUC LS emitter          emitters/fanuc_ls.py
  → [L] MakeTP (optional)         compilers/maketp.py
     → operator / ROBOGUIDE gate  (внешний диспетчер)
```

Обратную кинематику для планарного рисунка решает контроллер робота в реальном
времени; `svg2fanuc` работает только в декартовых координатах UFRAME холста.

## Тесты

```bash
pytest -q
```

Покрывают: secure gate (DTD/entity/href/`<text>`/fill/размер), viewBox и
transforms, адаптивный flattening и его лимит глубины, замкнутые контуры,
инверсию Y и выравнивание, routing (`preserve`/`nearest`/2-opt, «не хуже
исходного»), последовательность фаз, sharp corner → FINE, структуру LS и
дробление на подпрограммы, отказ на слишком большом штрихе, атомарность
вывода, коды завершения CLI, `verify`.

## Что осталось за рамками MVP

PNG и векторизация (модуль `png2svg`), заливки/градиенты/толщина штриха,
поддержание силы контакта, компенсация неплоскостности, автосмена инструмента,
собственная inverse kinematics, автозапуск робота, backend ROS 2 / MoveIt
(вторая очередь, раздел 14 спецификации).
