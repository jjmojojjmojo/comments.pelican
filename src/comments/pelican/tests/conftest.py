import pytest
import tempfile
import shutil
import os
import random

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
    
@pytest.fixture()
def fixed_seed():
    """
    Fix the random seed to a specific value (1)
    """
    random.seed(1)
    yield
    random.seed()