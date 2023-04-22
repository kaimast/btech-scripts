from ptree import PatriciaTree

def test_set_get():
    p = PatriciaTree()
    p.set(b"foo", b"bar")
    assert p.get(b"foo") == b"bar"

def test_multi_set():
    p = PatriciaTree()
    p.set(b"foo", b"bar")
    p.set(b"fab", b"hi")
    p.set(b"faz", b"hello")

    assert p.get(b"foo") == b"bar"
    assert p.get(b"faz") == b"hello"

def test_multi_set_long():
    p = PatriciaTree()
    p.set(b"foo", b"bar")
    p.set(b"fabababa", b"hi")

    p.print()

    assert p.get(b"fab") == None
    assert p.get(b"fabababa") == b"hi"


def test_clone():
    p = PatriciaTree()
    p.set(b"foo", b"bar")
    p2 = p.clone()
    assert p2.get(b"foo") == b"bar"
