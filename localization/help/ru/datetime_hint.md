# Ввод даты и времени
Иногда программа попросит ввести дату/время в форме строки. Это поле имеет свой особый, но понятный формат.
Вначале программа берёт уже существующую дату/время затем
## Легенда
Все указанные значения - целые числа
* Y - год
* M - месяц 
* D - день
* h - час
* m - минута
* s - секунда
* ms - миллисекунда
## Модификаторы
### Дата
* Y-M-D
* D.M.Y
* h:m:s
### Время
* h:m:s:ms
* h:m:s.ms
### Явное указание значения
Любую часть даты/времени можно явно указать с помощью модификатора <буква из легенды>=<значение>
## Примеры
### Поставить дату/время на 20 октября 2022 года, время 17:01:45
2022-10-20 17:01:45
## Установить полночь без изменения даты
0:0:0:0
или
0:0:0 ms=0