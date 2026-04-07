# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "goose-proxy"
author = "RHEL Lightspeed Team"

# Only the man page builder is used; no HTML output is generated.
man_pages = [
    # (source_file, name, description, authors, section)
    ("goose-proxy", "goose-proxy", "OpenAI Chat Completions to Responses API proxy", [author], 7),
    ("goose-proxy-config", "goose-proxy-config", "goose-proxy configuration file", [author], 5),
]
