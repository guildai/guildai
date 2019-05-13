{% set images = run|images -%}

{% if images -%}
{% for img in images -%}
![]({{ img.url }})

[{{ img.path }} ({{ img.size }})]({{ img.url }})
{% endfor %}
{% else -%}
There are no images for this run.
{%- endif %}
