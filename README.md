# Minimal R API for Python

[![pypi](https://img.shields.io/pypi/v/rapi.svg)](https://pypi.org/project/rapi/)
[![CircleCI](https://circleci.com/gh/randy3k/rapi/tree/master.svg?style=shield)](https://circleci.com/gh/randy3k/rapi/tree/master)

```py
import rapi
from rapi import rcopy, reval
rapi.start()
rcopy(reval("R.version"))
```
