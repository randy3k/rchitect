# Minimal R API for Python

[![CircleCI](https://circleci.com/gh/randy3k/rapi/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rapi/tree/master)
[![pypi](https://img.shields.io/pypi/v/rapi.svg)](https://pypi.org/project/rapi/)

```py
import rapi
from rapi import rcopy, reval
rapi.start()
rcopy(reval("R.version"))
```
