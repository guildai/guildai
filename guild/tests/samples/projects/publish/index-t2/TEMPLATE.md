Yet another index:

{% for run in runs -%}
- [{{ run.id }}]({{ run.id }}/README.md) - {{ run.operation }} {{ run.label or '' }}
{% endfor %}
