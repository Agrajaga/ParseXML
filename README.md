## Анализ выдачи поисковой системы авиаперелетов

В папке два XML – это ответы на поисковые запросы, сделанные к сайту via.com.
В ответах лежат варианты перелётов (тег `Flights`) со всей необходимой информацией,
чтобы отобразить билет на Aviasales.

Консольная утилита `parse_response.py` отвечает на вопросы:
* Какие варианты перелёта из DXB в BKK мы получили?
* Самый дорогой/дешёвый, быстрый/долгий и оптимальный варианты
* В чём отличия между результатами двух запросов (изменение маршрутов/условий)?

Формат ответа - `json`

Задание сделано на основе открытого тестового [задания](https://github.com/KosyanMedia/test-tasks/tree/master/assisted_team) из Aviasales.

### Способы использования

```
python parse_response.py -h
```
```
usage: parse_response.py [-h] [--human] (--all | --best | --compare file2) file1

Parse the XML response about flights from via.com and return JSON

positional arguments:
  file1            XML response from via.com

options:
  -h, --help       show this help message and exit
  --human          human-readable output
  --all            return all flight variants
  --best           return cheapest/expensive, fastest/slowest and optimal variants
  --compare file2  return differences in query parameters
```

### Цель проекта

Этот код написан в учебных целях на онлайн-курсах по web-разработке [dvmn.org](https://dvmn.org/).
