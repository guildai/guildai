# {{ run.operation }}

{{ run.started }}

## Attributes

{% include "_run_attrs.md" %}

{% if config.process_info|default(true) -%}
## Process Info

{% include "_run_process_info.md" %}
{%- endif %}

## Files

{% include "_files.md" %}

## Source

{% include "_source.md" %}
