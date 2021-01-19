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
  <v-app v-resize="onResize">
    <v-navigation-drawer
      app fixed clipped
      disable-route-watcher
      v-model="drawer"
      width="360"
      :mobile-break-point="drawerBreakPoint">
      <guild-view-select
        :runs="runs"
        v-model="selected"
        @input="maybeCloseDrawer" />
    </v-navigation-drawer>
    <guild-view-toolbar @drawer-click="drawer = !drawer" />
    <v-content>
      <guild-compare
        v-if="selected.compare"
        :compare="compare"
        @run-selected="run => { selected = {run: findRun(run)} }" />
      <guild-run
        v-else-if="selected.run"
        :run="selected.run" />
      <guild-view-waiting v-else />
    </v-content>
    <guild-view-footer :fixed="footerFixed" :config="config" />
  </v-app>
</template>

<script>
import { formatRuns } from './guild-runs.js';
import { fetchData } from './guild-data.js';

var drawerBreakPoint = 960;

export default {
  name: 'guild-view',

  data() {
    return {
      drawerBreakPoint: drawerBreakPoint,
      drawer: window.innerWidth >= drawerBreakPoint,
      footerFixed: window.innerWidth >= drawerBreakPoint,
      selected: {},
      runs: [],
      compare: [],
      config: {},
      fetchRunsTimeout: undefined
    };
  },

  created() {
    this.initData();
  },

  computed: {
    title() {
      var title = this.config.titleLabel;
      if (this.runs.length > 0 && !title.startsWith('[')) {
        title += ' (' + this.runs.length + ')';
      }
      title += ' - Guild View';
      return title;
    }
  },

  watch: {
    title(val) {
      document.title = val;
    }
  },

  methods: {
    onResize() {
      this.footerFixed = window.innerWidth >= drawerBreakPoint;
    },

    initData() {
      this.fetchConfig();
      this.fetchRuns();
    },

    fetchConfig() {
      var this_ = this;
      fetchData('/config', function(config) {
        this_.config = config;
      });
    },

    fetchRuns() {
      var this_ = this;
      fetchData('/runs', function(data) {
        this_.runs = formatRuns(data);
        this_.fetchCompare();
        this_.scheduleNextFetchRuns();
      });
    },

    fetchCompare() {
      var this_ = this;
      fetchData('/compare', function(data) {
        this_.compare = this_.formatCompare(data);
        // Calls to fetchCompare are called in handler of
        // fetchRuns so no need to schedule next call here.
      });
    },

    formatCompare(data) {
      return data;
    },

    scheduleNextFetchRuns() {
      if (this.fetchRunsTimeout) {
        clearTimeout(this.fetchRunsTimeout);
      }
      this.fetchRunsTimeout = setTimeout(this.fetchRuns, 5000);
    },

    maybeCloseDrawer() {
      if (window.innerWidth < drawerBreakPoint) {
        this.drawer = false;
      }
    },

    findRun(runOrId) {
      if (typeof runOrId === 'object') {
        return runOrId;
      }
      return this.runs.find(run => run.id.startsWith(runOrId));
    }
  }
};
</script>

<style>
.tabs__bar {
  padding: 0 16px !important;
}

table.datatable thead th {
  font-size: 13px;
  outline: none !important;
}

table.datatable thead th i {
  margin-left: 4px;
  color: #777 !important;
}

table.datatable thead tr {
  height: 42px;
}

table.datatable thead th {
  white-space: inherit;
}

table.datatable tbody td {
  font-size: 14px;
}
</style>
