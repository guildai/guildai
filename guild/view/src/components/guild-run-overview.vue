<template>
  <v-container fluid grid-list-lg>
    <v-layout row wrap>
      <v-flex xs12 lg7 xl8>
        <v-card>
          <v-card-text>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>ID</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.id }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Model</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.opModel }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Operation</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.opName }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Status</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">
                  {{ run.status }}
                  <template v-if="run.status === 'error'">
                    ({{ run.exitStatus }})
                  </template>
                </div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Started</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.started }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Stopped</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.stopped }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Time</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.time }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Label</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">{{ run.label }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Dependencies</v-subheader>
              </v-flex>
              <v-flex xs9 class="py-0">
                <div class="field-val">
                  <v-layout column>
                    <v-flex>
                      <template v-for="dep in run.deps">
                        <v-tooltip
                          bottom transition="fade-transition">
                          <div slot="activator">
                            <a
                              :href="'?run=' + dep.run"
                              target="_blank">{{ dep.operation }}</a>
                          </div>
                          <div>
                            <div>[{{ dep.run }}] {{ dep.operation }}</div>
                            <div v-for="path in dep.paths">
                              &ensp;&squf;&ensp;{{ path }}
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-flex>
                  </v-layout>
                </div>
              </v-flex>
            </v-layout>
          </v-card-text>
        </v-card>
        <v-card v-if="Object.keys(run.otherAttrs).length > 0" class="mt-3">
          <v-expansion-panel focusable>
            <v-expansion-panel-content :value="true">
              <div slot="header">Attributes</div>
              <v-card>
                <v-card-text>
                  <v-layout
                    row v-for="attr in otherAttrs" :key="attr.name">
                    <v-flex xs4 class="pa-0">
                      <v-subheader>{{ attr.name }}</v-subheader>
                    </v-flex>
                    <v-flex xs8 class="py-0">
                      <div class="field-val">
                        <v-tooltip bottom tag="div" class="no-wrap">
                          <div slot="activator" class="no-wrap">{{ attr.value }}</div>
                          <pre v-html="attr.value"></pre>
                        </v-tooltip>
                      </div>
                    </v-flex>
                  </v-layout>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-card>
      </v-flex>
      <v-flex xs12 lg5 xl4>
        <v-expansion-panel focusable v-if="scalars.length > 0">
          <v-expansion-panel-content :value="true">
            <div slot="header">Scalars</div>
            <v-card>
              <v-data-table
                :items="scalars"
                item-key="key"
                hide-headers
                hide-actions>
                <template slot="items" slot-scope="scalars">
                  <td>{{ scalars.item.key }}</td>
                  <td>{{ formatScalar(scalars.item.value) }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-expansion-panel-content>
        </v-expansion-panel>
        <v-expansion-panel focusable>
          <v-expansion-panel-content>
            <div slot="header">Flags</div>
            <v-card>
              <v-data-table
                :items="runFlags(run)"
                item-key="name"
                hide-headers
                hide-actions
                no-data-text="There are no flags for this run">
                <template slot="items" slot-scope="flags">
                  <td>{{ flags.item.name }}</td>
                  <td>{{ flags.item.value }}</td>
                </template>
              </v-data-table>
            </v-card>
          </v-expansion-panel-content>
        </v-expansion-panel>
        <v-expansion-panel focusable>
          <v-expansion-panel-content>
            <div slot="header">Command</div>
            <v-card>
              <v-card-text class="run-command">
                {{ run.command }}
              </v-card-text>
            </v-card>
          </v-expansion-panel-content>
        </v-expansion-panel>
        <v-expansion-panel focusable>
          <v-expansion-panel-content>
            <div slot="header">Env</div>
            <v-card>
              <v-data-table
                :items="runEnv(run)"
                item-key="name"
                hide-headers
                hide-actions
                no-data-text="There is no env for this run">
                <template slot="items" slot-scope="env">
                  <td>{{ env.item.name }}</td>
                  <td>
                    <v-tooltip left tag="div">
                      <span slot="activator" v-html="env.item.value">
                      </span>
                      <span v-html="env.item.value"></span>
                    </v-tooltip>
                  </td>
                </template>
              </v-data-table>
            </v-card>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
import { formatScalar } from './guild-runs.js';

export default {
  name: 'guild-run-overview',

  props: {
    run: {
      type: Object,
      required: true
    }
  },

  computed: {
    otherAttrs() {
      if (!this.run) {
        return [];
      }
      const attrs = this.run.otherAttrs;
      const names = Object.keys(attrs);
      names.sort();
      return names.map(name => ({name: name, value: attrs[name]}));
    },

    scalars() {
      const keys = ['step', 'val_acc', 'loss'];
      const scalars = keys.map(key => (
        {
          key: key,
          value: this.run.scalars[key]
        }
      ));
      return scalars.filter(scalar => scalar.value !== undefined);
    }
  },

  methods: {

    runFlags(run) {
      var keys = Object.keys(run.flags);
      keys.sort();
      return keys.map(key => ({ name: key, value: run.flags[key] }));
    },

    runEnv(run) {
      var keys = Object.keys(run.env);
      keys.sort();
      return keys.map(key => ({ name: key, value: envVal(run.env[key]) }));
    },

    formatScalar: formatScalar
  }
};

function envVal(s) {
  var breaks = s.match(/.{1,15}/g);
  return breaks ? breaks.join('&#8203;') : s;
}
</script>

<style scoped>
table.table tbody td {
  font-size: 14px;
}

.field-val {
  height: 48px;
  display: flex;
  align-items: center;
  word-break: break-all;
}

.field-val .no-wrap {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.run-command {
  font-family: monospace;
  font-size: 90%;
}

.expansion-panel__container {
  overflow: hidden;
}

.expansion-panel:not(:first-child) {
  margin-top: 16px;
}
</style>
