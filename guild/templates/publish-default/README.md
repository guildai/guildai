{% block header %}
[Published runs](../README.md)
{% endblock header %}

{% block body %}
{% block title %}
# {{ run.operation }}
{% endblock title %}

{% block summary%}
| ID                   | Operation           | Started                  | Time                | Status           | Label                |
| --                   | ---------           | ---------                | ----                | ------           | -----                |
| {{ run.id|short_id}} | {{ run.operation }} | {{ run.started|nbhyph }} | {{ run.time|nbsp }} | {{ run.status }} | {{ run.label|nbsp }} |

{% endblock summary %}

[run.yml](run.yml)

{% block contents %}
## Contents

- [Flags](#flags)
- [Scalars](#scalars)
- [Run Files](#run-files)
- [Source Code](#source-code)
- [Output](#output)

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

{% block sourcecode %}
## Source Code

{% include ["_sourcecode.md", "publish-default/_sourcecode.md"] %}
{% endblock sourcecode %}

{% block output %}
## Output

{% include ["_output.md", "publish-default/_output.md"] %}
{% endblock output %}

{#

{% block images %}
## Images

{% include ["_images.md", "publish-default/_images.md"] %}
{% endblock images %}

#}

{% endblock body %}

{% block footer %}
{% endblock footer %}
