#! /usr/bin/env python
import re
import ftplib
import os
import time


class TreeFile:
    def __init__(self, directory, name, size, modtime):
        self.dir = directory
        self.name = name
        self.size = size
        self.modtime = modtime
        self.ignored = False
        self.relpath = os.path.join(self.dir.relpath, self.name)
        self.abspath = os.path.join(self.dir.abspath, self.name)

    def __eq__(self, other):
        return self.dir == other.dir and self.name == other.name


class TreeDirectory:
    def __init__(self, parent, name, abspath):
        self.parent = parent
        self.name = name
        self.abspath = abspath
        self.ignored = False
        self.files = []
        self.subdirs = []
        if parent is None:
            self.relpath = self.name
            self.level = 0
        else:
            self.relpath = os.path.join(self.parent.relpath, self.name)
            self.level = parent.level + 1

    def __eq__(self, other):
        return self.parent == other.parent and self.name == other.name

    def addFile(self, name, size, modtime):
        file = TreeFile(self, name, size, modtime)
        self.files.append(file)
        return file

    def addSubdir(self, name):
        dir = TreeDirectory(self, name, os.path.join(self.abspath, name))
        self.subdirs.append(dir)
        return dir
