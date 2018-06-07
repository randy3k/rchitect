# Minimal R API for Python

[![CircleCI](https://circleci.com/gh/randy3k/rapi/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rapi/tree/master)
[![Build status](https://ci.appveyor.com/api/projects/status/4o9m8q61m755xc2a/branch/master?svg=true)](https://ci.appveyor.com/project/randy3k/rapi/branch/master)
[![pypi](https://img.shields.io/pypi/v/rapi.svg)](https://pypi.org/project/rapi/)

```py
import rapi
from rapi import rcopy, reval
rapi.start()
rcopy(reval("R.version"))
```


## R Eventloop in IPython

When running interactively in IPython, R events such as showing graphical 
devices could be handled by the `r` eventloop. Simply enter in IPython
```
%gui r
```
