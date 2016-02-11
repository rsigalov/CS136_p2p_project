#!/usr/bin/python

# Util functions ################

# http://stackoverflow.com/questions/5098580/implementing-argmax-in-python

from itertools import imap, izip, count
import math


def argmax(pairs):
    """
    given an iterable of pairs return the key corresponding to the greatest value
    """
    return max(pairs, key=lambda (a,b): b)[0]

 
def argmax_index(values):
    """
    given an iterable of values return the index of the greatest value
    """
    return argmax(izip(count(), values))

def argmax_f(keys, f):
    """
    given an iterable of keys and a function f, return the key with largest f(key)
    """
    return argmax((k, f(k)) for k in keys)

def argmax_f_tuples(keys, f):
    """
    given an iterable of key tuples and a function f, return the key with largest f(*key)
    """
    return max(imap(lambda key: (f(*key), key), keys))[1]

def mean(lst):
    """Throws a div by zero exception if list is empty"""
    return sum(lst) / float(len(lst))

def stddev(lst):
    if len(lst) == 0:
        return 0
    m = mean(lst)
    return math.sqrt(sum((x-m)*(x-m) for x in lst) / len(lst))


def median(numeric):
    vals = sorted(numeric)
    count = len(vals)
    if count % 2 == 1:
        return vals[(count+1)/2-1]
    else:
        lower = vals[count/2-1]
        upper = vals[count/2]
        return (float(lower + upper)) / 2

def proportional_split(n, lst):
    """
    n must be an int.
    lst is a list of integers that adds up to 100.
    returns a list of as-proportional-as-possible shares when n is divided into shares as in the lst.
    Excess is left for the end.
    >>> proportional_split(10,[54,36,10])
    [5,3,2]
    >>> proportional_split(3,[30,60,10])
    [0, 1,2]
    """
    ans = []
    if type(n) is not int:
        raise TypeError("n must be int")
    lst_sum = 0
    for i in lst:
        lst_sum += i
    if abs(lst_sum - 100) > 1e-5:
        raise TypeError("lst elements must add up to 100. It's %d", lst)
    ans = []
    last_split = n
    for i in lst[:-1]:
        ith_split = (n*i)//100
        ans.append(ith_split)
        last_split -= ith_split
    ans.append(last_split)
    return ans



def even_split(n, k):
    """
    n and k must be ints.
    
    returns a list of as-even-as-possible shares when n is divided into k pieces.

    Excess is left for the end.  If you want random order, shuffle the output.

    >>> even_split(2,1)
    [2]
    
    >>> even_split(2,2)
    [1, 1]

    >>> even_split(3,2)
    [1, 2]

    >>> even_split(11,3)
    [3, 4, 4]
    """
    ans = []
    if type(n) is not int or type(k) is not int:
        raise TypeError("n and k must be ints")

    r = n % k
    ans = ([n/k] * (k-r))
    ans.extend([n/k + 1] * r)
    return ans


def load_modules(agent_classes):
    """Each agent class must be in module class_name.lower().
    Returns a dictionary class_name->class"""

    def load(class_name):
        module_name = class_name.lower()  # by convention / fiat
        module = __import__(module_name)
        agent_class = module.__dict__[class_name]
        return (class_name, agent_class)

    return dict(map(load, agent_classes))
    


class Params:
    def __init__(self):
        self._init_keys = set(self.__dict__.keys())
    
    def add(self, k, v):
        self.__dict__[k] = v

    def __repr__(self):
        return "; ".join("%s=%s" % (k, str(self.__dict__[k])) for k in self.__dict__.keys() if k not in self._init_keys)
        


class IllegalUpload(Exception):
    pass

class IllegalRequest(Exception):
    pass




