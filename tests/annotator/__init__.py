from annotator.model import cleanup_all, setup_in_memory

def setup(self):
    setup_in_memory()

def teardown(self):
    cleanup_all(True)