{% block header %}
[Published runs](../README.md)
{% endblock header %}

{% block body %}
{% block title %}
# {{ run.operation }}
{% endblock title %}

{% block summary%}
| ID                   | Operation           | Started                  | Duration                | Status           | Label                |
| --                   | ---------           | ---------                | --------                | ------           | -----                |
| {{ run.id|short_id}} | {{ run.operation }} | {{ run.started|nbhyph }} | {{ run.duration|nbsp }} | {{ run.status }} | {{ run.label|nbsp }} |
{% endblock summary %}

[run.yml](run.yml)

{% block contents %}
## Contents

- [Flags](#flags)
- [Scalars](#scalars)
- [Run Files](#run-files)

{% endblock contents %}

{% block flags %}
## Flags

{% include ["_flags.md", "publish-default/_flags.md"] %}
{% endblock flags %}

{% block scalars %}
## Scalars

{% include ["_scalars.md", "publish-default/_scalars.md"] %}
{% endblock scalars %}

{% block runfiles %}
## Run Files

{% include ["_runfiles.md", "publish-default/_runfiles.md"] %}
{% endblock runfiles %}

{#

{% block images %}
## Images

{% include ["_images.md", "publish-default/_images.md"] %}
{% endblock images %}

{% block source %}
## Source Code

{% include ["_sourcecode.md", "publish-default/_source.md"] %}
{% endblock source %}

{% block attributes %}
## Attributes

{% include ["_run_attrs.md", "publish-default/_run_attrs.md"] %}
{% endblock attributes %}

#}

{% endblock body %}

{% block footer %}
{% endblock footer %}
