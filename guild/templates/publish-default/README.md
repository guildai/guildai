{% block header %}
[Published runs](../README.md)
{% endblock header %}

{% block body %}
{% block title %}
# {{ run.operation }}
{% endblock title %}

{% block summary%}
| ID                   | Operation           | Started                      | Duration                     | Status           | Label           |
| --                   | ---------           | ---------                    | --------                     | ------           | -----           |
| {{ run.id|short_id}} | {{ run.operation }} | {{ run.started|nb_hyphens }} | {{ run.duration|or_nbsp }} | {{ run.status }} | {{ run.label }} |
{% endblock summary %}

{#

{% block flags %}
## Flags

{% include ["_flags.md", "publish-default/_flags.md"] %}
{% endblock flags %}

{% block scalars %}
## Scalars

{% include ["_scalars.md", "publish-default/_scalars.md"] %}
{% endblock scalars %}

{% block files %}
## Files

{% include ["_files.md", "publish-default/_files.md"] %}
{% endblock files %}

{% block images %}
## Images

{% include ["_images.md", "publish-default/_images.md"] %}
{% endblock images %}

{% block source %}
## Source

{% include ["_source.md", "publish-default/_source.md"] %}
{% endblock source %}

{% block attributes %}
## Attributes

{% include ["_run_attrs.md", "publish-default/_run_attrs.md"] %}
{% endblock attributes %}

#}

{% endblock body %}

{% block footer %}
{% endblock footer %}
