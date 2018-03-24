<template>
  <v-container fluid grid-list-lg>
    <h4>{{ info.title }}</h4>
    <v-layout row wrap>
      <v-flex sm5>
        <div v-html="join(info.help)"></div>
      </v-flex>
      <v-flex sm7>
        <pre class="example">{{ join(info.example) }}</pre>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  name: 'guild-serve-example',

  props: {
    type: {
      type: String,
      required: true
    },
    endpoint: {
      type: String,
      required: true
    }
  },

  computed: {
    info() {
      if (this.type === 'curl-json-body') {
        return {
          title: 'POST JSON body',
          help: [
            'A JSON body must be a JSON-ecoded object ',
            'that conforms to the specification described in ',
            '<a href="https://cloud.google.com/ml-engine/docs/v1/' +
            'predict-request#request-body" target="_blank">Predict Request ',
            'Details</a>. Replace <code>{...}</code> with instance objects.',
            'The <code>Content-Type</code> request header ',
            'must be <code>application/json</code>.'
          ],
          example: [
            'curl ' + this.endpoint + ' \\',
            '  -H \'Content-Type: application/json\' \\',
            '  -d \'{"instances": [{...}, {...}]}\''
          ]
        };
      } else if (this.type === 'curl-json-object') {
        return {
          title: 'POST JSON object file',
          help: [
            'A JSON object file contains a single top-level JSON object ',
            'that conforms to the specification described in ',
            '<a href="https://cloud.google.com/ml-engine/docs/v1/' +
            'predict-request#request-body" target="_blank">Predict Request ',
            'Details</a>. Replace ',
            '<code>FILE</code> in the example with the path to the ',
            'JSON object file. The <code>Content-Type</code> request header ',
            'must be <code>application/json</code>.'
          ],
          example: [
            'curl ' + this.endpoint + ' \\',
            '  -H \'Content-Type: application/json\'',
            '  -d @FILE \\'
          ]
        };
      } else if (this.type === 'curl-json-instances') {
        return {
          title: 'POST json-instances file',
          help: [
            'A json-instances file contains one JSON-formatted instance per ',
            'line as described ',
            'in the <a href="https://cloud.google.com/sdk/gcloud/reference/' +
            'ml-engine/predict#--json-instances" target="_blank">' +
            'gcloud ml-engine predict</a> command documentation. Replace ',
            '<code>FILE</code> in the example with the path to the ',
            'json-instances file.'
          ],
          example: [
            'curl ' + this.endpoint + ' \\',
            '  -F json-instances=@FILE'
          ]
        };
      } else if (this.type === 'curl-text-instances') {
        return {
          title: 'POST text-instances file',
          help: [
            'A text-instances file contains one text-formatted instance per ',
            'line as described ',
            'in the <a href="https://cloud.google.com/sdk/gcloud/reference/' +
            'ml-engine/predict#--text-instances" target="_blank">' +
            'gcloud ml-engine predict</a> command documentation. Replace ',
            '<code>FILE</code> in the example with the path to the ',
            'text-instances file.'
          ],
          example: [
            'curl ' + this.endpoint + ' \\',
            '  -F text-instances=@FILE'
          ]
        };
      } else if (this.type === 'python-requests') {
        return {
          title: 'Requests',
          help: [
            '<a href="http://docs.python-requests.org/en/master/" ' +
            'target="_blank">Requests</a> is a popular Python library used ',
            'to make HTTP requests. This example illustrates how a JSON body ',
            'is submitted to the model endpoint.'
          ],
          example: [
            'import requests',
            '',
            'resp = requests.post(',
            '    "' + this.endpoint + '",',
            '    json={"instances": [{...}, {...}]})',
            '',
            'print(resp.status_code, resp.json())'
          ]
        };
      } else {
        return {};
      }
    }
  },

  methods: {
    join(lines) {
      return lines ? lines.join('\n') : '';
    }
  }
};
</script>
