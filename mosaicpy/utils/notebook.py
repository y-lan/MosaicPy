def setup_notebook(auto_reload=True):
    from IPython import get_ipython
    ipython = get_ipython()

    if auto_reload:
        ipython.run_line_magic('load_ext', 'autoreload')
        ipython.run_line_magic('autoreload', '2')
