"""
Basic functionality test of the data model.
"""

import pytest
import tempfile
import shutil
import os

from comments.pelican import data

@pytest.fixture(scope="session")
def fake_comments():
    """
    Write a few comments and threads to a temp directory for tests.
    """
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comments")
    
    path = tempfile.mkdtemp()
    
    shutil.copytree(source, path, dirs_exist_ok=True)
    
    yield path
    
    shutil.rmtree(path)

def test_load_thread_typical(fake_comments):
    """
    Load a properly formatted thread and look at its comments.
    """
    thread = data.Thread("article-1", COMMENTS_PATH=fake_comments)
    
    thread.load()
    
    assert thread.comments == [
        {'level': 0, 'order': 1, 'uid': 'ejzizpcog', 'parent': None}, 
        {'level': 0, 'order': 2, 'uid': 'jgpskmuex', 'parent': None}, 
        {'level': 1, 'order': 3, 'uid': 'jdycemcr', 'parent': 'jgpskmuex'}
    ]
    
def test_load_comment_typical(fake_comments):
    """
    Load a properly formatted comment.
    """
    thread = data.Thread("article-1", COMMENTS_PATH=fake_comments)
    
    comment = data.Comment(thread, 1, 3, "jdycemcr", "jgpskmuex")
    
    comment.load()
    
    assert comment.metadata['date'].isoformat() == '2016-02-11T23:40:22+00:00'
    assert comment.metadata['author'] == 'Jenifer Forcythe'
    
    assert comment.content == "<h1>Hello World</h1>\n<p>This is an example comment. It's formatted as markdown. It should <em>parse</em> properly.</p>"
    
    
def test_save_thread_typical(fake_comments, fixed_seed):
        """
        Create a new thread, add a few comments, and save it.
        """
        thread = data.Thread("test-99", COMMENTS_PATH=fake_comments)

        comment1 = thread.add()
        comment1.save(f"# First Top Comment {comment1.uid}")

        comment2 = thread.add(1, parent=comment1.uid)
        comment2.save(f"# First reply to {comment1.uid}, {comment2.uid}")

        comment3 = thread.add(1, parent=comment1.uid)
        comment3.save(f"# Second reply to {comment1.uid}, {comment3.uid}")

        comment4 = thread.add(1, parent=comment1.uid)
        comment4.save(f"# Third reply to {comment1.uid}, {comment4.uid}")

        comment5 = thread.add(1, parent=comment1.uid)
        comment5.save(f"# Fourth reply to {comment1.uid}, {comment5.uid}")

        comment6 = thread.add(2, parent=comment2.uid)
        comment6.save(f"# First reply to {comment2.uid}, {comment6.uid}")

        comment7 = thread.add(order=20)
        comment7.save(f"# Second Top Comment, {comment7.uid}")

        comment8 = thread.add(order=12)
        comment8.save(f"# Third Top Comment, {comment8.uid}")

        thread.save()

        with open(thread.thread_path, "r") as fp:
            content = fp.read()

       assert content == ""