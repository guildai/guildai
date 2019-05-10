| File | Size | Modified |
| ---- | ---- | -------- |
{% for file in run|source %}| [{{ file.path }}]({{ file.url }}) | {{ file.size }} | {{ file.modified }} |
{% endfor %}
