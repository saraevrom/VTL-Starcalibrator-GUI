# Datetime entry
Sometimes you will be asked to enter datetime as string. This entry field has special format but it is understandable.
Firstly program takes date that will be changed and applies modifiers written down in string field separated by spaces.
## Modifiers legend
All specified values are integers
* Y - year
* M - month 
* D - day
* h - hour
* m - minute
* s - second
* ms - millisecond
## Modifiers
### Date
* Y-M-D
* D.M.Y
* h:m:s
### Time
* h:m:s:ms
* h:m:s.ms
### Explicit modification
Every part of datetime can be set by modifier <letter from legend>=<value>
## Examples
### Set datetime to 20 of October 2022 17:01:45
2022-10-20 17:01:45
### Set time to midnight without changing date
0:0:0:0
or
0:0:0 ms=0