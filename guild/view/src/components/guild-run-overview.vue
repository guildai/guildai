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
              <v-flex xs9 class="pa-0">
                <div class="field-val">{{ run.id }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Model</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
                <div class="field-val">{{ run.opModel }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Operation</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
                <div class="field-val">{{ run.opName }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Status</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
                <div class="field-val">
                  {{ run.status }}
                  <template v-if="run.exitStatus">
                    ({{ run.exitStatus }})
                  </template>
                </div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Started</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
                <div class="field-val">{{ run.started }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Stopped</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
                <div class="field-val">{{ run.stopped }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Label</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
                <div class="field-val">{{ run.label }}</div>
              </v-flex>
            </v-layout>
            <v-layout row>
              <v-flex xs3 class="pa-0">
                <v-subheader>Dependencies</v-subheader>
              </v-flex>
              <v-flex xs9 class="pa-0">
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
                            <div v-for="path in dep.paths">&ensp;&squf;&ensp;{{ path }}</div>
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
      </v-flex>

      <v-flex xs12 lg5 xl4>
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

        <v-expansion-panel focusable class="mt-3">
          <v-expansion-panel-content>
            <div slot="header">Command</div>
            <v-card>
              <v-card-text class="run-command">
                {{ run.command }}
              </v-card-text>
            </v-card>
          </v-expansion-panel-content>
        </v-expansion-panel>

        <v-expansion-panel focusable class="mt-3">
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
 export default {
   name: 'guild-run-overview',

   props: {
     run: {
       type: Object,
       required: true
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
     }
   }
 };

 function envVal(s) {
   var breaks = s.match(/.{1,15}/g);
   return breaks ? breaks.join('&#8203;') : s;
 }
</script>

<style scoped>
 .field-val {
   height: 48px;
   display: flex;
   align-items: center;
   word-break: break-all;
 }

 .run-command {
   font-family: monospace;
   font-size: 90%;
 }
</style>
