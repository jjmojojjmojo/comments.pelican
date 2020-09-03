"""
Comment representative class and container of many comments.

Provides a template-friendly API for reading comments.

TODO: write comments as well?
TODO: process in parallel?
TODO: caching of already-processed comments that haven't changed?
TODO: use these classes to write out comments?

Usage:
    >>> from comments.pellican.data import Comment
    >>> comment = Comment(source_dir="/blog/path/comments")
    >>> comment.load()
    >>> comment.content
    >>> 'I agree'
    
    >>> from comments.pellican.data import Thread
    >>> comments = Comments("my-post", source_dir='/blog/path/comments')
    >>> comments.load()
    >>> [x for x in comments]
    [<Comment xxxxxxx>, <Comment yyyyyyyy>]
"""
import os
import markdown
import arrow
import textwrap
from collections import defaultdict

def sort_thread(thread):
    """
    Sort a thread list such that the comments could be printed in succession.
    """
    output = []
    
    by_level = {}
    
    def find_comment(thread, uid):
        """
        Given a comment UID, return it's place within the given thread
        """
        for i, comment in enumerate(thread):
            if comment['uid'] == uid:
                return i
                
        return -1
    
    # group the comments by level
    for comment in thread:
        if comment["level"] not in by_level:
            by_level[comment["level"]] = []
            
        by_level[comment["level"]].append(comment)
    
    for level in sorted(by_level.keys()):
        # if this is the first level, sort by order ascending.
        # else sort descending, since each child comment is inserted before the 
        # previous one.
        if level > 0:
            by_level[level].sort(key=lambda x: x['order'], reverse=True)
        else:
            by_level[level].sort(key=lambda x: x['order'])
            
        for comment in by_level[level]:
            # if there is no parent, just append, else find the parent
            # and insert after it.
            if comment['parent']:
                parent_loc = find_comment(output, comment['parent'])
                output.insert(parent_loc+1, comment)
            else:
                output.append(comment)
    
    return output

class Thread:
    """
    Container of comments. Can load comments from the filesystem for a given
    content slug.
    
    Implements iterator protocol, loop over each comment - comments are parsed in a lazy way.
    """
    
    def __init__(self, slug, **config):
        self.slug = slug
        self.config = config
        self.comments = []
        
    @property
    def comment_path(self):
        """
        Return the path to the comments for this thread
        """
        path = os.path.join(self.base_path, self.slug)
        
        path = os.path.abspath(path)
        
        assert os.path.exists(path), f"Comment path '{path}' missing or misconfigured"
        
        return path
        
    @property
    def base_path(self):
        """
        Return the main comments location (e.g. /path/my-blog/comments)
        
        TODO: is the current working directory always what we want?
        """
        path = self.config['COMMENTS_PATH']
        
        assert os.path.exists(path), f"Base path '{path}' missing or misconfigured"
        
        return path
        
    def __bool__(self):
        """
        True/False - False if no comments, True otherwise.
        """
        return bool(self.comments)
        
    @property
    def thread_path(self):
        path = os.path.join(self.base_path, f"{self.slug}.thread")
        
        assert os.path.exists(path), f"Thread file '{path}' missing or misconfigured"
        
        return path
        
    def load(self):
        comments = []
        
        try:
            with open(self.thread_path, 'r', encoding="utf-8") as thread:
                for line in thread:
                    comments.append(self._entry(line))
                    
            self.comments = sort_thread(comments)
        except AssertionError:
            self.comments = []
        
        
        
    def _entry(self, line):
        """
        Given a line from a thread file, return a dictionary containing 
        the comment data for the line.
        """
        parts = [x.strip() for x in line.split("\t")]
        
        entry = {        
            'level': int(parts[0]),
            'order': int(parts[1]),
            'uid': parts[2]
        }
        
        try:
            entry['parent'] = parts[3]
        except IndexError:
            entry['parent'] = None
            
        return entry
        
    def __iter__(self):
        """
        Generator to return comment objects
        
        Lazily loads/parses the content of each comment as its accessed.
        """
        for comment in self.comments:
            yield Comment(self, comment['level'], comment['order'], comment['uid'], comment['parent'])
            
    def __str__(self):
        """
        Return a console-printable view of this thread.
        """
        out = ""
        for comment in self:
            comment.load("markdown")
            author = comment.metadata.get("author", "Unknown")
            date = comment.metadata.get("date", "????-??-??")
            
            indent = "\t"*comment.level
            out += f"{indent}{author} wrote, at {date}\n"
            out += textwrap.indent(comment.content, indent*2)
            out += "\n\n"
        
        return out

class Comment:
    """
    Represents a single comment.
    
    Provides interface that should be easy to use in a template.
    
    Comment content is parsed and loaded when created.
    """
    
    def __init__(self, thread, level, order, uid, parent=None):
        """
        Constructor - read only
        """
        self.thread = thread
        self.level = int(level)
        self.order = int(order)
        self.uid = uid
        self.parent = parent
        self.metadata = {}
        
        self._content = ""
        self._loaded = False
    
    @property
    def content(self):
        if not self._loaded:
            self.load()
        
        return self._content
    
    @property
    def path(self):
        path = os.path.join(self.thread.comment_path, "%s.md" % (self.uid,))
        
        assert os.path.exists(path), "Comment path '%s' doesn't exist" % (path,)
        
        return path
    
    def _metadata(self, line):
        """
        Helper that takes a metadata line and returns a key/value tuple.
        
        Will parse known field names (such as date:) into python objects.
        """
        assert ":" in line, "Malformed metadata line, '%s'" % (line,)
        # split at colon, strip extraneous spaces
        key, val = [x.strip() for x in line.split(":", 1)]
        
        if key == "date":
            val = arrow.get(val).datetime
        
        return (key, val)
    
    def load(self, format='html5'):
        """
        Load the comment content and parse it via markdown
        
        Format can be any valid value you can pass to markdown.markdown
        (currently 'xhtml', 'html5').
        
        Alternatively, you can pass "markdown" to pass through the content 
        verbatim.
        
        TODO: format for the console.
        """
        if not self._loaded:
            with open(self.path, 'r') as source:
                for line in source:
                    if line.strip() == "":
                        break
                    else:
                        mkey, mval = self._metadata(line)
                        self.metadata[mkey] = mval
                
                content = source.read()
                if format == "markdown":
                    self._content = content
                else:
                    self._content = markdown.markdown(content, output_format=format)
                
            self._loaded = True