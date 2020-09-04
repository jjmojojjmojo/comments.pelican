"""
Testing comments.pelican.data.UIDMaker
"""

import pytest
from comments.pelican.data import UIDMaker
from comments.pelican import errors

def test_make_uid_no_load(fake_comments, fixed_seed):
    """
    Make a uid, no loading
    """
    uids = UIDMaker("article-2", COMMENTS_PATH=fake_comments)
    
    assert uids() == "pzmtyjszw"
    assert uids() == "elmsrwhnr"
    assert uids() == "jzocqdiqg"
    
    assert uids.uids == {'elmsrwhnr', 'jzocqdiqg', 'pzmtyjszw'}
    
def test_load_uids(fake_comments, fixed_seed):
    """
    Load the uids from a directory.
    """
    uids = UIDMaker("article-2", COMMENTS_PATH=fake_comments)
    
    uids.load()
    
    assert uids.uids == {'yjeuodfpw', 'mryhkgfer', 'mvvsxpukx', 'vrvtvjtkx', 'yxjfdocoo'}
    
def test_load_and_add(fake_comments, fixed_seed):
    """
    Load, and then add new uids.
    """
    uids = UIDMaker("article-2", COMMENTS_PATH=fake_comments)
    
    uids.load()
    uids()
    uids()
    uids()
    uids()
    
    assert uids.uids == {'vrvtvjtkx', 'nqouzyip', 'elmsrwhnr', 'mvvsxpukx', 'yjeuodfpw', 'yxjfdocoo', 'pzmtyjszw', 'jzocqdiqg', 'mryhkgfer'}
    
def test_failure_to_generate_unique_uid(monkeypatch, fake_comments, fixed_seed):
    """
    Contrive a situation where it's impossible to generate a unique uid
    """
    # patch the generate() method so it always returns the same thing
    monkeypatch.setattr(UIDMaker, "generate", lambda x: "generated")
    
    uids = UIDMaker("article-2", COMMENTS_PATH=fake_comments)
    
    with pytest.raises(errors.UIDTooManyRetries):
        uids()
        uids()
        
def test_generate_existing_without_retry(monkeypatch, fake_comments, fixed_seed):
    """
    Try to generate an existing uid with retry=False
    """
    # patch the generate() method so it always returns the same thing
    monkeypatch.setattr(UIDMaker, "generate", lambda x: "generated")
    uids = UIDMaker("article-2", COMMENTS_PATH=fake_comments)
    
    assert uids(False) == "generated"
    
    with pytest.raises(errors.UIDExists):
        uids(False)
    