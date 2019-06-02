{% set rows = scalars|csv_dict_rows -%}

{% if rows -%}
| Key | Step | Value |
| --- | ---- | ----- |
{% for row in rows %} | {{ row|scalar_key }} | {{ row.last_step|nbsp }} | {{ row.last_val|nbsp }} |
{% endfor %}
[scalars.csv](scalars.csv)
{% else -%}
There are no scalars for this run.
{%- endif %}
