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
import glob
import random
import operator
from . import errors

from hashids import Hashids

class SlugMixin:
    """
    Common code for classes that work with a slug-based directory.
    
    API assumes your instances have the following variables:
    - config, dict (configuration settings)
    - slug, string (content slug)
    
    TODO: add separate checks for existence, code to create dirs if they don't exist.
    """
    @property
    def comment_path(self):
        """
        Return the path to the comments for this thread
        """
        path = os.path.join(self.base_path, self.slug)
        
        path = os.path.abspath(path)
        
        return path
        
    @property
    def base_path(self):
        """
        Return the main comments location (e.g. /path/my-blog/comments)
        """
        path = self.config['COMMENTS_PATH']
        
        return path
        
    @property
    def thread_path(self):
        path = os.path.join(self.base_path, f"{self.slug}.thread")
        
        return path
    
    
class UIDMaker(SlugMixin):
    """
    Generates unique UIDs. Keeps an in-memory log of existing and previously
    generated UIDs for the given thread slug.
    
    NOTE: this is not thread-safe, be careful using it in parallel operations.
    
    TODO: use some other mechanism besides scanning files to get existing
          UIDs
    TODO: broadcast events when finding/generating a new UID to make sync easier.
    TODO: add config to control hashid alphabet
    """
    def __init__(self, slug, **config):
        self.slug = slug
        self.config = config
        self.uids = set()
        self.hashids = Hashids(alphabet='abcdefghijklmnopqrstuvwxyz')
        self.max_retries = 10
        
    def load(self):
        """
        Scan a comment directory and load all of the existing uids.
        """
        for path in glob.iglob(os.path.join(self.comment_path, "*.md")):
            uid = os.path.splitext(os.path.basename(path))[0]
            self.uids.add(uid)
            
    def generate(self):
        """
        Create a random hashid
        """
        return self.hashids.encode(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
    def __call__(self, retry=True):
        """
        Generate a hash id and return it.
        
        Verifies that it isn't already in the list, and will re-generate up to 10 times
        unless retry=False. In that case, raises UIDExists.
        """
        tries = 0
        while True:
            tries += 1
            uid = self.generate()
            if uid in self.uids:
                if not retry:
                    raise errors.UIDExists(f"UID {uid} already in use")
                
                if tries > self.max_retries:
                    raise errors.UIDTooManyRetries(f"Unique UID could not be generated after {tries} attempts")
            else:
                self.uids.add(uid)
                return uid
                
    
    

class Thread(SlugMixin):
    """
    Container of comments. Can load comments from the filesystem for a given
    content slug.
    
    Implements iterator protocol, loop over each comment - comments are parsed in a lazy way.
    
    TODO: make inline version that doesn't load the entire thread into memory, instead
          read each comment from the file as requested
    """
    encoding = "utf-8"
    
    def __init__(self, slug, **config):
        self.slug = slug
        self.config = config
        self.comments = []
        self.uids = UIDMaker(slug)
        
        # store the comment with the highest order for each level
        self.levels = {}
        self.dummies = []
        
        self.next = 0
        
    def __bool__(self):
        """
        True/False - False if no comments, True otherwise.
        """
        return bool(self.comments)
        
    def load(self):
        self.comments = []
        
        with open(self.thread_path, 'r', encoding=self.encoding) as thread:
            for line in thread:
                parsed = self._entry(line)
                comment = self.add(parsed['level'], parsed['order'], parsed['uid'], parsed['parent'])
    
    def find(self, uid, level):
        """
        Find a comment in the thread, for the given level.
        """
        comment = DummyComment(self, uid=uid, level=level)
        try:
            location = self.comments.index(comment)
            return location, self.comments[location]
        except ValueError:
            comment.order = self.next
            self.next += 1
            self.dummies.append(uid)
            return None, comment
    
    def insert_into_level(self, subject):
        """
        Insert a given comment into its set level
        """
        location = None
        
        parent_loc = None
        level_end = None
        largest = 0
        
        for index, comment in enumerate(self.comments):
            if comment.uid == subject.parent:
                parent_loc = index
            
            if comment.level == subject.level:
                level_end = index
            
            if comment.parent == subject.parent:
                if comment.order >= largest and comment.order <= subject.order:
                    location = index
                    largest = comment.order
        
        if location is None:
            location = -1
            
            if parent_loc is not None and subject.level != 0:
                location = parent_loc+1
                
            #if level_end is not None:
            #    if self.comments[level_end].order <= subject.order:
            #        location = level_end
            #    else:
            #        location = level_end+1
            
        self.comments.insert(location, subject)
        return location
    
    def replace_dummy(self, comment):
        """
        When a real comment comes in, that will replace a dummy comment, we need
        to properly insert it, but first collect all of its current descendants.
        """
        
        loc, dummy = self.find(comment.uid, comment.level)

        self.comments.remove(dummy)
        
        children = []
        temp = self.comments[:loc]
        save = True
        for index in range(loc, len(self.comments)):
            child = self.comments[index]
            
            if child.level == dummy.level:
                save = False
            
            if save:
                children.append(child)
            else:
                temp.append(child)
            
        self.dummies.remove(comment.uid)
        
        self.comments = temp
        
        loc = self.insert(comment)
        
        for index in range(len(children)-1, -1, -1):
            self.comments.insert(loc+1, children[index])
        
        return loc
    
    def insert(self, comment):
        """
        Place a comment where it belongs in the thread.
        """
        if comment.uid in self.dummies:
            return self.replace_dummy(comment)
        
        if comment.parent:
            position, parent = self.find(comment.parent, comment.level-1)
            comment.level = parent.level+1
            
            if position is None:
                # no parent found, insert new dummy parent into end of level
                position = self.insert_into_level(parent)
            
            return self.insert_into_level(comment)
        else:
            return self.insert_into_level(comment)
    
    def add(self, level=0, order=None, uid=None, parent=None):
        """
        Add a Comment object to the list of comments
        
        TODO: insert in correct location to maintain sort?
        TODO: check parent, see if the level is correct?
        """
        if order is None:
            order = self.next
            self.next += 1
        elif order > self.next:
            self.next = order + 1
        
        comment = Comment(self, level=level, order=order, uid=uid, parent=parent)
        
        self.insert(comment)
        return comment
        
    def save(self):
        """
        Write out the thread to disk.
        """
        os.makedirs(self.comment_path, exist_ok=True)
        
        with open(self.thread_path, "w") as fp:
            for index, comment in enumerate(self):
                print(f"{comment.level}\t{comment.order}\t{comment.uid}\t{comment.parent}", file=fp)
                
            self.next = index+1
        
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
        
        TODO: lazy load from the file
        """
        for comment in self.comments:
            yield comment
            
    def __str__(self):
        """
        Return a console-printable view of this thread.
        """
        out = ""
        for comment in self:
            comment.load(ignore_errors=True)
            author = comment.metadata.get("author", "Unknown")
            date = comment.metadata.get("date", "????-??-??")
            
            indent = "\t"*comment.level
            out += f"{indent}{author} wrote, at {date} [{comment.uid}, {comment.order}]\n"
            out += textwrap.indent(comment.parse("markdown"), indent*2)
            out += "\n\n"
        
        return out

class Comment:
    """
    Represents a single comment.
    
    Provides interface that should be easy to use in a template.
    
    Comment content is parsed and loaded when created.
    
    TODO: handle encodings beside UTF-8
    """
    encoding = "utf-8"
    
    def __init__(self, thread, level=0, order=0, uid=None, parent=None):
        """
        Constructor - read only
        """
        self.thread = thread
        
        self.level = int(level)
        if self.level < 0:
            self.level = 0
        
        self.order = int(order)
        if self.order < 0:
            self.order = 0
        
        self._metadata = {}
        
        self._content = ""
        self._loaded = False
        
        if uid is None:
            self.uid = thread.uids()
        else:
            self.uid = uid
            
        if parent is None:
            parent = ""
        self.parent = parent
    
    @property
    def metadata(self):
        """
        TODO: load metadata only by just scanning the top of the file
        
        TODO: don't load metadata if the object wasn't read from disk
        """
        return self._metadata
    
    @property
    def content(self):
        """
        TODO: only load content from the file by skipping metadata.
        
        TODO: don't load content if the object wasn't read from disk
        """
        return self._content
    
    def parse(self, format="html5"):
        """
        Convert the raw markdown source to HTML for display.
        
        Format can be any valid value you can pass to markdown.markdown
        (currently 'xhtml', 'html5').
        
        Alternatively, you can pass "markdown" to pass through the content 
        verbatim.
        
        TODO: format for the console, strip out tags.
        """
        if format == "markdown":
            return self._content
        else:
            return markdown.markdown(self._content, output_format=format)
    
    @property
    def exists(self):
        assert os.path.exists(path), "Comment path '%s' doesn't exist" % (path,)
    
    @property
    def path(self):
        path = os.path.join(self.thread.comment_path, "%s.md" % (self.uid,))
        
        return path
    
    def _parse_metadata(self, line):
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
    
    def load(self, format='html5', ignore_errors=False):
        """
        Load the comment content
        """
        if not self._loaded:
            try:
                with open(self.path, 'r') as source:
                    for line in source:
                        if line.strip() == "":
                            break
                        else:
                            mkey, mval = self._parse_metadata(line)
                            self.metadata[mkey] = mval
                    
                    self._content = source.read()
            except IOError:
                if ignore_errors:
                    self._content = "[[deleted]]"
                else:
                    raise
                
            self._loaded = True
            
    def save(self, content=None):
        """
        Write out the comment with the given content.
        
        TODO: don't overwrite if already exists
        TODO: optionally update/set the date
        TODO: check if content or metadata has changed, don't bother if not.
        """
        os.makedirs(self.thread.comment_path, exist_ok=True)
        
        if content is not None:
            self._loaded = True
            self._content = content
        
        with open(self.path, 'w', encoding=self.encoding) as output:
            for key, val in self.metadata.items():
                output.write("%s: %s\n" % (key, val))
                
            output.write("\n")
            
            if type(self.content) == bytes:
                output.write(self.content.decode(self.encoding))
            else:
                output.write(self.content)
                
    def __repr__(self):
        return f'<{self.__class__.__name__} uid="{self.uid}" level="{self.level}" order="{self.order}" parent="{self.parent}">'
        
    def __eq__(self, b):
        return self.uid == b.uid
        
class DummyComment(Comment):
    """
    Marker class to differentiate comments created or loaded from ones that
    are are just temporary place holders
    """
