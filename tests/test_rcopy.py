import rapi
from rapi import rcopy, reval
rapi.start()

def test_rcopy():
    assert rcopy(reval("5")) == 5
