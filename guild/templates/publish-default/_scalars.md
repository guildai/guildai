| Key | Step | Value |
| --- | ---- | ----- |
{% for s in run|scalars %}| {{ s|scalar_key }} | {{ s.last_step }} | {{ s.last_val }} |
{% endfor %}
