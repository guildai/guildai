{% set run_files = run|files -%}

{% if run_files -%}
| File | Size | Modified |
| ---- | ---- | -------- |
{% for file in run_files %}| [{{ file.path }}]({{ file.url }}) | {{ file.size }} | {{ file.modified }} |
{% endfor %}
{% else -%}
There are no files for this run.
{%- endif %}
