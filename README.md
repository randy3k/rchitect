# Minimal R API for Python

[![CircleCI](https://circleci.com/gh/randy3k/rapi/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rapi/tree/master)
[![pypi](https://img.shields.io/pypi/v/rapi.svg)](https://pypi.org/project/rapi/)

```py
import rapi
from rapi import rtopy, reval
rapi.start()
rtopy(reval("R.version"))
```


## R Eventloop in IPython

When running interactively in IPython, R events such as showing graphical 
devices could be handled by the `r` eventloop. Simply enter in IPython
```
%gui r
```
