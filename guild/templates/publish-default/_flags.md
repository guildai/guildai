{% set flags = run|flags -%}

{% if flags -%}
| Name | Value |
| ---- | ----- |
{% for name, val in flags %}| {{ name}} | {{ val }} |
{% endfor %}
{% else -%}
There are no flags for this run.
{%- endif %}
