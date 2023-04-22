"""
Simplified implementation of a Patricia tree.

Some simplifications:
    * Root node is always a branch
    * Does not embed nodes in other
    * On-disk format less space-efficient but easier to understand
"""

from hashlib import sha3_256

import rlp

BITS_PER_NIBBLE = 4
BRANCHING_FACTOR = pow(2, BITS_PER_NIBBLE)

def bytes_to_nibbles(key: bytes) -> [int]:
    assert isinstance(key, bytes)

    result = []
    for byte in key:
        result.append(byte % BRANCHING_FACTOR)
        result.append(byte // BRANCHING_FACTOR)

    return result

class Branch:
    def __init__(self):
        """ A branch in the tree. Can have multiple children and also a leaf """

        self.children = [None for _ in range(BRANCHING_FACTOR)]
        self.data = None
        self.hash = None

    def get(self, path: [int]):
        if len(path) == 0:
            return self.data

        idx = path.pop(0)
        if self.children[idx] is None:
            return None

        return self.children[idx].get(path)

    def set(self, path: [int], data: bytes):
        """ Add a new child to this branch """
        assert self.hash is None

        if len(path) == 0:
            self.data = data
            return

        idx = path.pop(0)
        child = self.children[idx]

        if child is None:
            self.children[idx] = Leaf(path, data)
        elif isinstance(child, Branch):
            child.set(path, data)
        elif isinstance(child, Extension):
            pos = 0
            while len(child.path) > pos and len(path) > 0 and path[0] == child.path[pos]:
                path.pop(0)
                pos += 1

            if len(child.path) == pos:
                child.child.set(path, data)
            else:
                branch = Branch()
                branch.set(path, data)
                branch.set(child.path[pos:], child.child)

                if pos > 0:
                    newext = child.path[:pos]
                    self.children[idx] = Extension(newext, branch)
                else:
                    self.children[idx] = branch

        elif isinstance(child, Leaf):
            pos = 0
            while len(child.suffix) > pos and len(path) > 0 and path[0] == child.suffix[pos]:
                path.pop(0)
                pos += 1

            if len(child.suffix) == pos and len(path) == 0:
                child.data = data
            else:
                branch = Branch()
                branch.set(path, data)
                branch.set(child.suffix[pos:], child.data)

                if pos > 0:
                    newext = child.suffix[:pos]
                    self.children[idx] = Extension(newext, branch)
                else:
                    self.children[idx] = branch
        else:
            raise RuntimeError("Invalid state!")

    def seal(self):
        to_hash = []

        for child in self.children:
            if child is None:
                to_hash.append(0)
            else:
                to_hash.append(child.seal())

        if self.data is None:
            to_hash.append(0)
        else:
            to_hash.append(self.data)

        encoded = rlp.encode(to_hash)

        hasher = sha3_256()
        hasher.update(encoded)

        self.hash = hasher.digest()
        return self.hash

    def clone(self):
        """ Create a unsealed copy of this branch """

        newbranch = Branch()
        for (idx, child) in enumerate(self.children):
            if child is not None:
                newbranch.children[idx] = child.clone()
        newbranch.data = self.data
        return newbranch

    def is_sealed(self) -> bool:
        return self.hash is not None

    def print(self):
        child_idx = []
        for (idx, child) in enumerate(self.children):
            if child is not None:
                child_idx.append(hex(idx))
        print(f"Branch with children at {child_idx} and data={self.data}")
        for child in self.children:
            if child is not None:
                child.print()

class Extension:
    """ An extension node that compacts a part of the tree without branching """

    def __init__(self, path: [int], child):
        self.path = path
        self.child = child
        self.hash = None

    def seal(self):
        child_hash = self.child.seal()
        to_hash = [self.path, child_hash]

        encoded = rlp.encode(to_hash)

        hasher = sha3_256()
        hasher.update(encoded)

        self.hash = hasher.digest()
        return self.hash

    def print(self):
        print(f"Extension with path={[hex(p) for p in self.path]}")
        self.child.print()

    def get(self, path: [int]):
        if len(path) < len(self.path):
            return None

        prefix = path[:len(self.path)]
        if prefix != self.path:
            return None

        return self.child.get(path[len(self.path):])

    def clone(self):
        """ Create a unsealed copy of this extension """

        newchild = self.child.clone()
        return Extension(self.path, newchild)

class Leaf:
    """ A leaf node with an (optional) suffix. Directly holds data. """

    def __init__(self, suffix: [int], data: bytes):
        self.suffix = suffix
        self.data = data
        self.hash = None

    def seal(self):
        to_hash = [self.suffix, self.data]

        encoded = rlp.encode(to_hash)

        hasher = sha3_256()
        hasher.update(encoded)

        self.hash = hasher.digest()
        return self.hash

    def print(self):
        print(f"Leaf with suffix={[hex(s) for s in self.suffix]} and data={self.data}")

    def set(self, path: [int], data: bytes):
        assert self.hash is None
        assert path == self.suffix
        self.data = data

    def get(self, path: [int]):
        if path != self.suffix:
            return None

        return self.data

    def clone(self):
        """ Create a unsealed copy of this leaf """
        return Leaf(self.suffix, self.data)

class PatriciaTree:
    def __init__(self, prev=None):
        if prev:
            self.root = prev.root.clone()
        else:
            self.root = Branch()

    def is_sealed(self) -> bool:
        return self.root.is_sealed()

    def set(self, key: bytes, data: bytes):
        if self.is_sealed():
            raise RuntimeError("Already sealed!")

        nkey = bytes_to_nibbles(key)
        self.root.set(nkey, data)

    def clone(self): # -> PatriciaTree:
        """
        Start building a new block from the sealed a
        Will perform copy on write for all changes done
        """
        return PatriciaTree(prev=self)

    def get(self, key: bytes):
        nkey = bytes_to_nibbles(key)
        return self.root.get(nkey)

    def print(self):
        self.root.print()

    def seal(self):
        return self.root.seal()
