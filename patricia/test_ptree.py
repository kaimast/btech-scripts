from ptree import PatriciaTree

def test_set_get():
    p = PatriciaTree()
    p.set(b"foo", b"bar")
    assert p.get(b"foo") == b"bar"

def test_clone():
    p = PatriciaTree()
    p.set(b"foo", b"bar")
    p2 = p.clone()
    assert p2.get(b"foo") == b"bar"
