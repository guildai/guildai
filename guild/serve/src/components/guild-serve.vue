<template>
  <v-app>
    <v-toolbar fixed app clipped-left class="indigo darken-1 white--text">
      <v-toolbar-title>Guild Serve</v-toolbar-title>
    </v-toolbar>
    <v-content>
      <v-tabs class="signatures">
        <div class="grey lighten-4">
          <v-container fluid pl-4 pb-2>
            <h1>{{ modelTitle }}</h1>
            <div>TensorFlow v{{ model.tensorflow_ver }}</div>
            <div>{{ model.date }}</div>
            <div class="mt-1 grey--text text--darken-2">{{ model.path }}</div>
          </v-container>
          <v-tabs-bar>
            <v-tabs-item key="overview" href="#overview" ripple>predict images</v-tabs-item>
            <v-tabs-item key="files" href="#files" ripple>serving default</v-tabs-item>
            <v-tabs-slider color="deep-orange"></v-tabs-slider>
          </v-tabs-bar>
          <v-divider/>
        </div>
        <v-tabs-items>
          <v-tabs-content key="overview" id="overview">
            <v-expansion-panel :expand="true">
              <v-expansion-panel-content value="true">
                <div slot="header">Endpoint</div>
                <v-card>
                  <v-card-text>
                    <pre class="endpoint">http://localhost:8082/predict_images</pre>
                  </v-card-text>
                </v-card>
              </v-expansion-panel-content>
              <v-expansion-panel-content value="true">
                <div slot="header">Inputs</div>
                <v-card>
                  <v-card-text>
                    <v-data-table
                      :items="model.inputs"
                      :headers="tensorHeaders"
                      no-data-text="There are no inputs for this signature"
                      hide-actions>
                      <template slot="items" slot-scope="inputs">
                        <td>{{ inputs.item.name }}</td>
                        <td>{{ inputs.item.dtype }}</td>
                        <td>{{ inputs.item.shape }}</td>
                        <td>{{ inputs.item.tensor }}</td>
                      </template>
                    </v-data-table>
                  </v-card-text>
                </v-card>
              </v-expansion-panel-content>
              <v-expansion-panel-content value="true">
                <div slot="header">Outputs</div>
                <v-card>
                  <v-card-text>
                    Lorem ipsum dolor sit amet, consectetur adipiscing
                    elit, sed do eiusmod tempor incididunt ut labore
                    et dolore magna aliqua. Ut enim ad minim veniam,
                    quis nostrud exercitation ullamco laboris nisi ut
                    aliquip ex ea commodo consequat.
                  </v-card-text>
                </v-card>
              </v-expansion-panel-content>
              <v-expansion-panel-content value="true">
                <div slot="header">Examples</div>
                <v-card>
                  <v-card-text class="examples">
                    <v-tabs>
                      <div>
                        <v-tabs-bar>
                          <v-tabs-item key="curl" href="#curl" ripple>curl</v-tabs-item>
                          <v-tabs-item key="python" href="#python" ripple>python</v-tabs-item>
                          <v-tabs-slider color="deep-orange"></v-tabs-slider>
                        </v-tabs-bar>
                        <v-divider/>
                      </div>
                      <v-tabs-items>
                        <v-tabs-content key="curl" id="curl">
                          <v-card>
                            <v-card-text>

                              <v-subheader>
                                POST&nbsp;<a href="#" class="help">JSON body</a>
                              </v-subheader>
                              <pre class="example">curl http://localhost:8082/predict_images -d '{"instances": [{...}, {...}]}'</pre>

                              <v-container fluid grid-list-lg>
                                <h4>POST JSON object file</h4>
                                <v-layout row wrap>
                                  <v-flex sm4>
                                    <div>
                                      Lorem ipsum dolor sit amet, consectetur adipiscing
                                      elit, sed do eiusmod tempor
                                      incididunt ut labore et dolore
                                      magna aliqua.
                                    </div>
                                  </v-flex>
                                  <v-flex sm8>
                                    <pre class="example">curl http://localhost:8082/predict_images -d @FILE</pre>
                                  </v-flex>
                                </v-layout>
                              </v-container>

                              <v-container fluid grid-list-lg>
                                <h4>POST json-instances file</h4>
                                <v-layout row wrap>
                                  <v-flex sm8>
                                    <pre class="example">curl http://localhost:8082/predict_images -F @json-instances=FILE</pre>
                                  </v-flex>
                                  <v-flex sm4>
                                    <div>
                                      Lorem ipsum dolor sit amet, consectetur adipiscing
                                      elit, sed do eiusmod tempor
                                      incididunt ut labore et dolore
                                      magna aliqua.
                                    </div>
                                  </v-flex>
                                </v-layout>
                              </v-container>


                              <v-subheader>
                                POST json-instances file
                                <v-btn flat small icon color="grey" class="help">
                                  <v-icon>help</v-icon>
                                </v-btn>
                              </v-subheader>
                              <pre class="example">curl http://localhost:8082/predict_images -F @json-instances=FILE</pre>

                              <v-subheader>
                                POST text-instances file
                                <v-btn flat small icon color="grey" class="help">
                                  <v-icon>help</v-icon>
                                </v-btn>
                              </v-subheader>
                              <pre class="example">curl http://localhost:8082/predict_images -F @text-instances=FILE</pre>

                            </v-card-text>
                          </v-card>
                        </v-tabs-content>
                      </v-tabs-items>
                    </v-tabs>
                  </v-card-text>
                </v-card>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-tabs-content>
          <v-tabs-content key="files" id="files">
            <div>Another thing</div>
          </v-tabs-content>
        </v-tabs-items>
      </v-tabs>
    </v-content>
    <v-footer fixed app color="grey lighten-2">
      <v-layout column justify-center style="margin:0">
        <v-divider />
        <v-layout align-center class="px-2 caption" style="height:36px">
          <div>{{ config.cwd }}</div>
          <v-spacer />
          <div v-show="config.version">Guild AI v{{ config.version }}</div>
        </v-layout>
      </v-layout>
    </v-footer>
  </v-app>
</template>

<script>
export default {
  name: 'guild-serve',

  data() {
    return {
      tensorHeaders: [
        { text: 'Name', value: 'name', align: 'left' },
        { text: 'Type', value: 'dtype', align: 'left' },
        { text: 'Shape', value: 'shape', align: 'left' },
        { text: 'Tensor', value: 'tensor', align: 'left' }
      ],
      config: {
        cwd: '~/foo/bar',
        version: '0.3.1.dev6'
      },
      model: {
        tags: ['serve'],
        name: 'census/1521721235',
        date: '2018-03-22 07:18:33',
        path: '/home/garrett/.guild/runs/233878262dcb11e88decc85b764bbf34/export/census/1521721235',
        tensorflow_ver: '1.4.0',
        inputs: [],
        outputs: []
      }
    };
  },

  computed: {
    modelTitle() {
      return this.model.tags.join(', ') + ' - ' + this.model.name;
    }
  },

  created() {
    document.title = this.modelTitle;
  }
};
</script>

<style>
.signatures {
  height: 100%;
  background: #fff;
}

pre.endpoint {
  margin: 0 10px 10px;
  background: #f5f5f5;
  padding: 10px 15px;
  font-size: 13px;
  white-space: pre-wrap;
}

pre.example {
  background: #f5f5f5;
  padding: 10px 15px;
  font-size: 13px;
  white-space: pre-wrap;
}

.expansion-panel__header {
  color: rgba(0,0,0,0.54);
}

.examples.card__text {
  padding-top: 0;
}

.examples.card__text .tabs__item {
  font-size: 12px;
}

.examples h4 {
  color: rgba(0,0,0,0.54);
  font-weight: 400;
}

.btn.help {
  margin-left: 4px;
}

.btn.help .icon {
  font-size: 18px;
}

.application a.help {
  color: inherit;
  text-decoration-style: dotted;
}
</style>
