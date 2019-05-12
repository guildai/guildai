# {{ run.operation }}

{{ run.started }}

## Attributes

{% include "_run_attrs.md" %}

{% if config.process_info|default(true) -%}
## Process Info

{% include "_run_process_info.md" %}
{%- endif %}

## Flags

{% include "_flags.md" %}

## Scalars

{% include "_scalars.md" %}

## Files

{% include "_files.md" %}

## Images

{% include "_images.md" %}

## Source

{% include "_source.md" %}
