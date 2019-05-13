{% set source = run|source -%}

{% if source -%}
| File | Size | Modified |
| ---- | ---- | -------- |
{% for file in source %}| [{{ file.path }}]({{ file.url }}) | {{ file.size }} | {{ file.modified }} |
{% endfor %}
{% else -%}
There are no source files for this run.
{%- endif %}
