"""
Basic functionality test of the data model.
"""

from comments.pelican import data
import os
import arrow
import shutil

def test_load_thread_typical(fake_comments):
    """
    Load a properly formatted thread and look at its comments.
    """
    thread = data.Thread("article-1", COMMENTS_PATH=fake_comments)
    
    thread.load()
    
    assert thread.comments == [
        data.Comment(thread, uid="jgpskmuex"),
        data.Comment(thread, uid="jdycemcr"),
        data.Comment(thread, uid="ejzizpcog")
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
    
    assert comment.parse() == "<h1>Hello World</h1>\n<p>This is an example comment. It's formatted as markdown. It should <em>parse</em> properly.</p>"
    

def test_save_comment_typical(fake_comments, fixed_seed):
    """
    Create a new comment and save it.
    """
    thread = data.Thread("test-1", COMMENTS_PATH=fake_comments)
    os.makedirs(thread.comment_path)
    
    comment = data.Comment(thread, level=0, order=12, uid=None, parent=None)
    comment.metadata['author'] = "Random Person"
    comment.metadata['date'] = arrow.get("2020-01-01").datetime
    comment.save("""
        # Hello World
        
        * This
        * is 
        * great
    """)
    
    comment_path = os.path.join(fake_comments, "test-1", f"{comment.uid}.md")
    
    assert os.path.exists(comment_path)
    
    with open(comment_path, "r") as fp:
        comment_file = fp.read()
        
    assert comment_file == 'author: Random Person\ndate: 2020-01-01 00:00:00+00:00\n\n\n        # Hello World\n        \n        * This\n        * is \n        * great\n    '
    
    
def test_save_thread_typical(fake_comments, fixed_seed):
    """
    Create a new thread, add a few comments, and save it.
    """
    thread = data.Thread("test-99", COMMENTS_PATH=fake_comments)
    
    comment1 = thread.add()
    comment1.save(f"# First Top Comment {comment1.uid}")
    
    comment2 = thread.add(parent=comment1.uid)
    comment2.save(f"# First reply to {comment1.uid}, {comment2.uid}")
    
    comment3 = thread.add(parent=comment1.uid)
    comment3.save(f"# Second reply to {comment1.uid}, {comment3.uid}")
    
    comment4 = thread.add(parent=comment1.uid)
    comment4.save(f"# Third reply to {comment1.uid}, {comment4.uid}")
    
    comment5 = thread.add(parent=comment1.uid)
    comment5.save(f"# Fourth reply to {comment1.uid}, {comment5.uid}")
    
    comment6 = thread.add(parent=comment2.uid)
    comment6.save(f"# First reply to {comment2.uid}, {comment6.uid}")
    
    comment7 = thread.add(debug=True)
    comment7.save(f"# Second Top Comment, {comment7.uid}")
    
    comment8 = thread.add()
    comment8.save(f"# Third Top Comment, {comment8.uid}")
    
    thread.save()
    
    with open(thread.thread_path, "r") as fp:
        content = fp.read()
        
    assert content == '0\t7\trmspuo\t\n0\t6\tppjikkto\t\n0\t0\tpzmtyjszw\t\n1\t4\tdwzizlcx\tpzmtyjszw\n1\t3\tnqouzyip\tpzmtyjszw\n1\t2\tjzocqdiqg\tpzmtyjszw\n1\t1\telmsrwhnr\tpzmtyjszw\n2\t5\tqjyhxofln\telmsrwhnr\n'
    
    
def test_load_randomized_thread(fake_comments, fixed_seed):
    """
    Load a comment thread that has been shuffled before saving.
    
    This simulates writes to the thread file out of order.
    """
    thread = data.Thread("article-random", COMMENTS_PATH=fake_comments)
    
    thread.load()
    
    assert [(x.uid, x.level, x.order) for x in thread.comments] == [
        ('third-top', 0, 10),
        ('second-top', 0, 9),
        ('first-top', 0, 0),
            ('second-nested', 1, 5),
                ('second-3', 2, 8),
                ('second-2', 2, 7),
                ('second-1', 2, 6),
            ('first-5', 1, 4),
            ('first-4', 1, 3),
            ('first-3', 1, 2),
            ('first-2', 1, 1)
    ]
    