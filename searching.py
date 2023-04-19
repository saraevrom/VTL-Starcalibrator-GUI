import numpy as np


def comparing_binsearch(array,target):
    start = 0
    end = len(array)
    middle = (start+end)//2
    while start!=middle:
        if target<array[middle]:
            end = middle
            middle = (start+end)//2
        elif target>array[middle]:
            start = middle
            middle = (start+end)//2
        else:
            return middle

    return middle