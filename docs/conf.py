import sphinx_rtd_theme

project = u'Guild AI'
copyright = u'2017, TensorHub, Inc'
version = u'0.2.0.dev4'
author = u'Guild AI'

master_doc = 'index'
html_theme = 'sphinx_rtd_theme'
html_context = {
    "show_sphinx": False
}

# The following are temporarily disabled until the docs fill in. Will
# cleanup in time.

"""
templates_path = ['_templates']
extensions = ['sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages']
source_suffix = '.rst'
release = u'0.2.0.dev4'
language = None
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = 'sphinx'
todo_include_todos = True
html_theme_options = {}
html_static_path = ['_static']
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}
htmlhelp_basename = 'GuildAIdoc'
"""
