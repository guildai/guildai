/* Copyright 2017-2023 Posit Software, PBC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

<template>
  <v-container fluid grid-list-lg>
    <v-card>
      <v-card-title class="py-0">
        <v-spacer />
        <v-text-field
          append-icon="search"
          label="Filter"
          single-line
          hide-details
          clearable
          v-model="filter"
          style="max-width:20em;margin-bottom:-8px" />
      </v-card-title>
      <v-data-table
        ref="table"
        class="run-output"
        :headers="headers"
        :items="lines"
        :search="filter"
        item-key="index"
        :hide-headers="lines.length == 0"
        hide-actions
        must-sort
        no-data-text="There is no output associated with this run"
        no-results-text="No matches for the current filter">
        <template slot="items" slot-scope="lines">
          <tr :class="'stream-' + lines.item[1]">
            <td class="time">{{ formatTime(lines.item[0]) }}</td>
            <td class="val">{{ lines.item[2] }}</td>
          </tr>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script>
import { fetchData } from './guild-data.js';

export default {
  name: 'guild-run-output',

  props: {
    run: {
      type: Object,
      required: true
    }
  },

  data() {
    return {
      filter: '',
      headers: [
        { text: 'Time', align: 'left', value: '0', sortable: true },
        { text: '', align: 'left', value: '2', sortable: false }
      ],
      fetchTimeout: undefined,
      curRunId: undefined,
      nextStart: 0,
      lines: []
    };
  },

  created() {
    this.curRunId = this.run.id;
    this.init();
  },

  watch: {
    run(val) {
      if (val.id !== this.curRunId) {
        this.curRunId = val.id;
        this.init();
      }
    }
  },

  methods: {
    init() {
      this.nextStart = 0;
      this.lines = [];
      this.fetchOutput();
    },

    fetchOutput() {
      var vm = this;
      const url = '/runs/' + vm.run.id + '/output?s=' + vm.nextStart;
      fetchData(url, function(output) {
        output.forEach(line => {
          vm.lines.push(line);
        });
        vm.nextStart += output.length;
        vm.scheduleNextFetch();
      });
    },

    scheduleNextFetch() {
      if (this.fetchTimeout) {
        clearTimeout(this.fetchTimeout);
      }
      this.fetchTimeout = setTimeout(this.fetchOutput, 5000);
    },

    formatTime(time) {
      const date = new Date(time);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
  }
};
</script>

<style>
.run-output table.table td {
  height: unset;
  padding: 5px 15px !important;
  vertical-align: top;
}

.run-output table td.time {
  white-space: nowrap;
  font-size: 13px;
}

.run-output table td.val {
  width: 99%;
  font-family: monospace;
  font-size: 13px;
}

.run-output table tr.stream-1 td.val {
  color: #616161;
}
</style>
