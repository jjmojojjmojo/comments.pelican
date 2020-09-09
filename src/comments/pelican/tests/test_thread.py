"""
Unit tests for various methods of the Thread class.
"""

import pytest
from comments.pelican.data import DummyComment, Comment, Thread
from pprint import pprint

def test_insert_into_level_normal(fake_comments, fixed_seed):
    """
    Insert a Comment into the correct place among its level peers.
    
    Most common use cases.
    """
    thread = Thread("test-99", COMMENTS_PATH=fake_comments)
    
    comment1 = Comment(thread, level=0, order=200, uid="comment1")
    comment2 = Comment(thread, uid="comment2", parent="comment1", level=1)
    comment3 = Comment(thread, uid="comment3", level=0, order=100)
    
    thread.comments = [comment1, comment2, comment3]
    
    # insert into level 0, an older comment
    comment4 = Comment(thread, uid="comment4", level=0, order=150)
    
    thread.insert_into_level(comment4)
    #                          0,200     1,0       0,150     0,100
    assert thread.comments == [comment1, comment2, comment4, comment3]
    
    # insert into level 0, a newer comment
    comment5 = Comment(thread, uid="comment5", level=0, order=99)
    
    thread.insert_into_level(comment5)
    #                          0,200     1,0       0,150     0,100     0,99
    assert thread.comments == [comment1, comment2, comment4, comment3, comment5]
    
    

def test_replace_dummy(fake_comments, fixed_seed):
    """
    Insert a Comment into the correct place among its level peers.
    """
    thread = Thread("test-99", COMMENTS_PATH=fake_comments)
    
    comment1 = Comment(thread, level=0, order=200, uid="comment1")
    comment2 = Comment(thread, uid="comment2", parent="comment1", level=1)
    comment3 = Comment(thread, uid="comment3", level=0, order=100)
    comment10 = DummyComment(thread, uid="comment10", level=0)
    
    thread.dummies.append("comment10")
    
    comment4 = Comment(thread, uid="comment4", level=1, order=1, parent="comment10")
    comment5 = Comment(thread, uid="comment5", level=1, order=0, parent="comment10")
    comment6 = Comment(thread, uid="comment6", level=2, order=0, parent="comment5")
    
    thread.comments = [comment10, comment4, comment5, comment6, comment1, comment2, comment3]
    
    real_comment10 = Comment(thread, uid="comment10", level=0, order=150)
    
    thread.replace_dummy(real_comment10)
    
    assert thread.comments == [
        comment1, comment2, comment10, comment4, comment5, comment6, comment3
    ]
    