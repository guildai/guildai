| File | Size |
| ---- | ---- |
{% for file in run|files %}| [{{ file.path }}]({{ file.url }}) | {{ file.size }} |
{% endfor %}
