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
  <v-container fluid>
    <h1 class="mb-2">Compare runs</h1>
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
          style="max-width:20em;margin-bottom:-12px" />
      </v-card-title>
      <v-data-table
        class="compare-runs"
        :headers="headers"
        :items="runs"
        :pagination.sync="pagination"
        :search="filter"
        item-key="id"
        hide-actions
        must-sort
        no-data-text="There are currently no runs to compare"
        no-results-text="No matches for the current filter">
        <template slot="items" slot-scope="run">
          <tr>
            <template v-for="val, index in run.item">
              <td v-if="index == 'run'">
                <a href="javascript:void(0)"
                   @click.prevent="$emit('run-selected', val)"
                >{{ val }}</a>
              </td>
              <td v-else>{{ tryFormatScalar(val) }}</td>
            </template>
          </tr>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script>
import { tryFormatScalar } from './guild-runs.js';

export default {

  name: 'guild-compare',

  props: {
    compare: {
      type: Array,
      required: true
    }
  },

  data() {
    return {
      filter: '',
      pagination: {
        sortBy: 'started',
        descending: true,
        rowsPerPage: -1
      }
    };
  },

  computed: {
    headers() {
      if (!this.compare.length) {
        return [];
      }
      var row1 = this.compare[0];
      return row1.map(name => (
        {text: this.formatHeader(name), value: name, align: 'left'}
      ));
    },

    runs() {
      if (!this.compare.length) {
        return [];
      }
      var row1 = this.compare[0];
      return this.compare.slice(1).map(data => this.runsRow(data, row1));
    }
  },

  methods: {
    tryFormatScalar: tryFormatScalar,

    formatHeader(s) {
      const cap = [
        'run', 'operation', 'started', 'time',
        'status', 'label', 'sourcecode'];
      if (cap.includes(s)) {
        return s.charAt(0).toUpperCase() + s.slice(1);
      }
      return s;
    },

    runsRow(data, headers) {
      var row = {};
      headers.forEach(function(name, index) {
        row[headers[index]] = data[index];
      });
      return row;
    }
  }
};
</script>

<style>
.compare-runs > table.table thead th {
  font-size: 13px;
  outline: none !important;
}

.compare-runs > table.table thead th i {
  margin-left: 4px;
  color: #777 !important;
}

.compare-runs table.table tbody td {
  font-size: 14px;
}

.compare-runs table.table tbody td.nowrap {
  white-space: nowrap;
}

.compare-runs > table.table thead tr {
  height: 48px;
}
</style>
