"""
Parse comments into a template variable that can be iterated over.

Comments are assumed to be stored in individual files, in the following structure:

settings.COMMENTS_DIRECTORY (defaults to root of blog/comments)
    [article-slug].thread # json representing structure of parents/children
    article-slug/         # individual markdown files containing each comment
        random-comment-id.md
        child1-id.md
        
TODO: better control over configuration
TODO: put comment into into objects/dicts for easier use by jinja
TODO: where to put comment metadata? (author, date/time)
"""

from pelican import signals
from comments.pelican import data

def inject_comments(article_generator):
    for article in article_generator.articles:
        thread = data.Thread(article.slug, **article.settings)
        article.comments = thread
        article.comments.load()
        
def register():
    signals.article_generator_finalized.connect(inject_comments)