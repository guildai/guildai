{% set scalars = run|scalars -%}

{% if scalars -%}
| Key | Step | Value |
| --- | ---- | ----- |
{% for s in scalars %}| {{ s|scalar_key }} | {{ s.last_step }} | {{ s.last_val }} |
{% endfor %}
{% else -%}
There are no scalars for this run.
{%- endif %}
