{% include "_msg.txt" %}

{% for run in runs %}- [{{ run.id }}]({{ run.id }}/README.md) - {{ run.operation }}
{% endfor %}
