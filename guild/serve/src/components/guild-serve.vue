<template>
  <v-app v-resize="onResize">
    <v-navigation-drawer
      app fixed clipped
      disable-route-watcher
      v-model="drawer"
      width="320"
      :mobile-break-point="drawerBreakPoint">

      <v-list two-line>
        <v-list-tile class="model-info">
          <v-list-tile-content>
            <v-tooltip
              top transition="fade-transition"
              tag="div">
              <h1 slot="activator" class="model-title">
                <span style="word-break:break-all">{{ modelTitle }}</span>
                <span style="white-space: nowrap">{{ modelTags }}</span>
              </h1>
              <span>{{ model.path }}</span>
            </v-tooltip>
            <v-list-tile-sub-title>
              TensorFlow v{{ model.tensorflowVersion }}
            </v-list-tile-sub-title>
          </v-list-tile-content>
        </v-list-tile>

        <v-subheader>Signature Defs</v-subheader>
        <v-divider />
        <template v-for="sig in signatureDefs">
          <v-list-tile
            :key="sig.key"
            @click="selected_ = sig"
            :class="{selected: selected === sig}"
            ripple>
            <v-list-tile-content>
              <v-list-tile-title>{{ sig.key }}</v-list-tile-title>
              <v-list-tile-sub-title>
                {{ sig.methodName }}
              </v-list-tile-sub-title>
            </v-list-tile-content>
          </v-list-tile>
          <v-divider />
        </template>
      </v-list>
    </v-navigation-drawer>

    <v-toolbar fixed app clipped-left class="indigo darken-1 white--text">
      <v-toolbar-side-icon class="white--text" @click="drawer = !drawer" />
      <v-toolbar-title>Guild Serve</v-toolbar-title>
      <v-spacer />
    </v-toolbar>

    <v-content>
      <v-tabs v-if="selected" class="signatures">

        <div class="grey lighten-4">
          <v-container fluid pl-4 pb-2>
            <h1>{{ selected.key }}</h1>
            <div class="grey--text text--darken-2">
              {{ model.path }} {{ modelTags }}
            </div>
          </v-container>
          <v-tabs-bar>
            <v-tabs-item key="overview" href="#endpoint" ripple>
              Endpoint
            </v-tabs-item>
            <v-tabs-item key="inputs" href="#inputs" ripple>
              Inputs
            </v-tabs-item>
            <v-tabs-item key="outputs" href="#outputs" ripple>
              Outputs
            </v-tabs-item>
            <v-tabs-slider color="deep-orange"></v-tabs-slider>
          </v-tabs-bar>
          <v-divider />
        </div>

        <v-tabs-items>
          <v-tabs-content key="endpoint" id="endpoint">
            <v-card>
              <v-card-text>
                <pre class="endpoint">{{ selected.endpoint }}</pre>
                <h3>Usage examples</h3>
                <v-expansion-panel>
                  <v-expansion-panel-content :value="true">
                    <div slot="header" class="mono">curl</div>
                    <v-card>
                      <v-card-text>
                        <guild-serve-example
                          type="curl-json-body"
                          :endpoint="selected.endpoint" />
                        <guild-serve-example
                          type="curl-json-object"
                          :endpoint="selected.endpoint" />
                        <guild-serve-example
                          type="curl-json-instances"
                          :endpoint="selected.endpoint" />
                        <guild-serve-example
                          type="curl-text-instances"
                          :endpoint="selected.endpoint" />
                      </v-card-text>
                    </v-card>
                  </v-expansion-panel-content>
                  <v-expansion-panel-content>
                    <div slot="header">Python</div>
                    <v-card>
                      <v-card-text>
                        <guild-serve-example
                          type="python-requests"
                          :endpoint="selected.endpoint" />
                      </v-card-text>
                    </v-card>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-card-text>
            </v-card>
          </v-tabs-content>

          <v-tabs-content key="inputs" id="inputs">
            <v-card>
              <v-card-text>
                <guild-select-tensors :tensors="selected.inputs" />
              </v-card-text>
            </v-card>
          </v-tabs-content>

          <v-tabs-content key="outputs" id="outputs">
            <v-card>
              <v-card-text>
                <guild-select-tensors :tensors="selected.outputs" />
              </v-card-text>
            </v-card>
          </v-tabs-content>
        </v-tabs-items>
      </v-tabs>
    </v-content>

    <v-footer :fixed="footerFixed" app color="grey lighten-2">
      <v-layout column justify-center style="margin:0">
        <v-divider />
        <v-layout align-center class="px-2 caption" style="height:36px">
          <div>{{ ctx.cwd }}</div>
          <v-spacer />
          <div v-show="ctx.version">Guild AI v{{ ctx.version }}</div>
        </v-layout>
      </v-layout>
    </v-footer>
  </v-app>
</template>

<script>
var drawerBreakPoint = 960;

export default {
  name: 'guild-serve',

  data() {
    return {
      drawerBreakPoint: drawerBreakPoint,
      drawer: window.innerWidth >= drawerBreakPoint,
      footerFixed: window.innerWidth >= drawerBreakPoint,
      selected_: undefined,
      ctx: {},
      model: {}
    };
  },

  computed: {
    modelTitle() {
      if (!this.model || !this.model.path) {
        return '';
      }
      const parts = this.model.path.split('/');
      if (parts.length >= 2) {
        return parts.slice(parts.length - 2).join('/');
      } else {
        return parts[parts.length - 1];
      }
    },

    modelTags() {
      if (!this.model || !this.model.tags) {
        return '';
      }
      const tags = this.model.tags.concat();
      tags.sort();
      return '(' + tags.join(', ') + ')';
    },

    signatureDefs() {
      return this.model.signatureDefs ? this.model.signatureDefs : [];
    },

    selected() {
      if (this.selected_) {
        return this.selected_;
      } else if (this.signatureDefs.length > 0) {
        return this.signatureDefs[0];
      } else {
        return undefined;
      }
    }
  },

  watch: {
    model(val) {
      document.title = val.path + ' - Guild View';
    }
  },

  created() {
    this.initData();
  },

  methods: {
    onResize() {
      this.footerFixed = window.innerWidth >= drawerBreakPoint;
    },

    initData() {
      const this_ = this;
      this.fetch(process.env.SERVE_BASE + '/ctx.json', data => {
        this_.ctx = data;
      });
      this.fetch(process.env.SERVE_BASE + '/model.json', data => {
        this_.model = data;
        if (data.signatureDefs && data.signatureDefs.length > 0) {
          this_.selectedSig = data.signatureDefs[0];
        } else {
          this_.selectedSig = null;
        }
      });
    },

    fetch(url, cb) {
      fetch(url).then(function(resp) {
        return resp.json();
      }).then(function(data) {
        cb(data);
      });
    },

    requestsExample(sig) {
      const lines = [
        'import requests',
        '',
        'resp = requests.post(',
        '    "' + sig.endpoint + '",',
        '    json={"instances": [{...}, {...}]})',
        '',
        'print(resp.json())'
      ];
      return lines.join('\n');
    }
  }
};
</script>

<style>
.model-info .list__tile {
  height: unset !important;
  padding: 16px !important;
}

.model-info .model-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 6px;
}

div.toolbar__title {
  margin-left: 6px;
}

.navigation-drawer li.selected {
  background-color: #f5f5f5;
}

.signatures {
  height: 100%;
  background: #fff;
}

pre {
  font-family: 'Roboto Mono', monospace;
  border-radius: 2px;
  padding: 10px 15px;
  font-size: 13px;
  white-space: pre;
  overflow: auto;
  word-wrap: normal;
}

pre.endpoint {
  background: #f5f5f5;
  color: #bd4147;
  margin: 0 10px 10px;
}

pre.example {
  background: #6d6d6d;
  color: #fff;
}

pre.sample {
  background: #f5f5f5;
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

h3 {
  font-weight: normal;
  margin: 20px 0 20px;
}

code {
  box-shadow: none;
}

.mono {
  font-family: 'Roboto Mono', monospace;
}
</style>
