# Minimal R API for Python

[![pypi](https://img.shields.io/pypi/v/rapi.svg)](https://pypi.org/project/rapi/)
[![Build Status](https://travis-ci.org/randy3k/rapi.svg?branch=master)](https://travis-ci.org/randy3k/rapi)

```py
import rapi
from rapi import rcopy, reval
rapi.start()
rcopy(reval("R.version"))
```
