{% set run_files = run|files -%}

{% if run_files -%}
| File | Size | Modified |
| ---- | ---- | -------- |
{% for file in run_files %}| {% if file.url %}[{{ file.path }}]({{ file.url }}){% else %}{{ file.path }}{% endif %} {% if file.islink %}{% if file.url %}<small>(link)</small>{% else %}<small>(link - target missing)</small>{% endif %}{% endif %} | {{ file.size }} | {{ file.modified }} |
{% endfor %}
{% else -%}
There are no files for this run.
{%- endif %}
