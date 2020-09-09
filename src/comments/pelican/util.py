"""
Utilities.
"""

from . import data
import random


class ThreadGenerator:
    def __init__(self, slug, comments_path):
        self.thread = data.Thread(slug, COMMENTS_PATH=comments_path)
        
        self._counter = -1
        
    
    @property
    def counter(self):
        self._counter += 1
        return self._counter
        
    def generate_children(self, parent, depth=5, count=2):
        level = parent.level + 1
        
        if level > depth:
            print(parent)
            return
            
        for x in range(count):
            order = self.counter
            uid = f"child-{level}-{order}"
            child = self.thread.add(level=level, order=order, uid=uid, parent=parent.uid)
            self.generate_children(child, depth, count)
        
    def generate_thread(self, depth=2, count=2, child_count=1):
        """
        Randomly-generate a thread and populate it with random comments.
        """
        for x in range(count):
            order = self.counter
            uid = f"parent-0-{order}"
            parent = self.thread.add(level=0, order=order, uid=uid, parent=None)
            self.generate_children(parent, depth, child_count)