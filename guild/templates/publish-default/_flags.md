{% if flags -%}
| Name | Value |
| ---- | ----- |
{% for name, val in flags|dictsort %}| {{ name }} | {{ val }} |
{% endfor %}
[flags.yml](flags.yml)
{% else -%}
There are no flags for this run.
{%- endif %}
