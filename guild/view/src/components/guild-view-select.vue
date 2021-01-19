/* Copyright 2017-2021 TensorHub, Inc.
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
  <v-list>
    <v-subheader>Runs</v-subheader>
    <v-list-tile>
      <div style="width:100%; margin-top:-24px; margin-bottom:-6px">
        <v-text-field
          v-model="filter"
          append-icon="search"
          label="Filter"
          single-line
          hide-details
          clearable
          style="font-weight:400"
        />
      </div>
    </v-list-tile>
    <v-divider />
    <v-list-tile ripple @click="tensorboard" class="tile-button">
      <v-list-tile-content>
        <v-tooltip top transition="fade-transition" tag="div" >
          <v-list-tile-title slot="activator">
            <v-icon style="margin-top:-3px" color="deep-orange darken-1">timeline</v-icon>
            View in TensorBoard
          </v-list-tile-title>
          <span>View runs in TensorBoard</span>
        </v-tooltip>
      </v-list-tile-content>
    </v-list-tile>
    <v-divider />
    <v-list-tile
      @click="select({compare: true})"
      :class="{selected: selected.compare}"
      ripple>
      <v-list-tile-content>
        <v-tooltip top transition="fade-transition" tag="div" >
          <v-list-tile-title slot="activator">
            <v-icon style="margin-top:-3px" color="light-blue darken-1">mdi-sort</v-icon>
            Compare runs
          </v-list-tile-title>
          <span>Compare runs</span>
        </v-tooltip>
      </v-list-tile-content>
    </v-list-tile>
    <v-divider />
    <template v-for="run in filteredRuns">
      <v-list-tile
        :key="run.id"
        @click="select({run: run})"
        :class="{selected: selected.run && selected.run.id === run.id}"
        ripple>
        <v-list-tile-content>
          <v-tooltip
            top transition="fade-transition"
            tag="div"
            class="rev-ellipsis-container">
            <v-list-tile-title slot="activator" class="rev-ellipsis">
              &lrm;{{ run.operation }}
              <span v-if="run.label" class="run-title-label">
                {{ run.label }}
              </span>
            </v-list-tile-title>
            <span>[{{ run.shortId }}] {{ run.operation }}</span>
          </v-tooltip>
          <v-list-tile-sub-title>{{ run.started }}</v-list-tile-sub-title>
        </v-list-tile-content>
        <v-list-tile-action style="min-width: 28px">
          <guild-run-status-icon :icon="run.icon" tooltip-right />
        </v-list-tile-action>
      </v-list-tile>
      <v-divider />
    </template>
  </v-list>
</template>

<script>
export default {
  name: 'guild-view-select',

  props: {
    runs: {
      type: Array,
      required: true
    },
    value: {
      type: Object,
      default: {}
    }
  },

  data() {
    return {
      filter: ''
    };
  },

  computed: {
    filteredRuns() {
      if (!this.filter) {
        return this.runs;
      }
      const filter = this.filter.toLowerCase();
      return this.runs.filter(run => {
        const text = (
          run.operation.toLowerCase() +
          run.label.toLowerCase() +
          run.id);
        return text.indexOf(filter) !== -1;
      });
    },

    selected() {
      if (this.value.compare) {
        return this.value;
      } else {
        const runs = this.filteredRuns;
        if (this.value.run) {
          const selectedRun = runs.find(run => run.id === this.value.run.id);
          if (selectedRun) {
            return {run: selectedRun};
          }
        }
        return runs.length > 0 ? {run: runs[0]} : {};
      }
    }
  },

  watch: {
    selected(val) {
      if (JSON.stringify(val) !== JSON.stringify(this.value)) {
        this.$emit('input', val);
      }
    }
  },

  methods: {
    select(val) {
      this.$emit('input', val);
    },

    tensorboard() {
      const qs = window.location.search;
      window.open(
        process.env.VIEW_BASE + '/tb/' + qs,
        'guild-tb-' + qs);
    }
  }
};
</script>

<style>
.list__tile {
  height: inherit;
  padding: 10px 16px;
}

.run-title-label {
  color: rgba(0,0,0,0.54);
  margin-right: 10px;
  float: right;
}

.rev-ellipsis-container {
  width: 100%;
}

.rev-ellipsis {
  direction: rtl;
}

li.selected {
  background-color: #f5f5f5;
}

.runs-view-in-tensorboard {
  position: absolute;
  top: 12px;
  right: 0;
}
</style>
