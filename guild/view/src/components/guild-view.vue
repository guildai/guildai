<template>
  <v-app >
    <v-navigation-drawer
      app fixed clipped
      v-model="drawer"
      width="360"
      :mobile-break-point="drawerBreakPoint">
      <guild-view-select
        :runs="runs"
        v-model="run"
        @input="maybeCloseDrawer" />
    </v-navigation-drawer>
    <guild-view-toolbar @drawer-click="drawer = !drawer" />
    <v-content>
      <guild-run v-if="run" :run="run" />
      <v-container v-else>
        <v-layout row align-center>
          <span class="mr-3">Waiting for runs</span>
          <v-progress-circular indeterminate color="primary" size="18"/>
        </v-layout>
      </v-container>
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
 import { formatRuns } from './guild-runs.js';
 import { fetchData } from './guild-data.js';

 var drawerBreakPoint = 960;

 export default {
   name: 'guild-view',

   data() {
     return {
       drawerBreakPoint: drawerBreakPoint,
       drawer: window.innerWidth >= drawerBreakPoint,
       runId_: undefined,
       runs: [],
       config: {},
       fetchRunsTimeout: undefined
     };
   },

   created() {
     this.initData();
   },

   computed: {
     run: {
       get() {
         this.checkRunDeleted();
         if (this.runId_) {
           return this.findRun(this.runId_);
         } else if (this.runs) {
           return this.runs[0];
         } else {
           return undefined;
         }
       },
       set(val) {
         this.runId_ = val ? val.id : undefined;
       }
     },

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
       fetchData('/runs', function(runs) {
         this_.runs = formatRuns(runs);
         this_.scheduleNextFetchRuns();
       });
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

     findRun(id) {
       return this.runs.find(run => run.id === id);
     },

     checkRunDeleted() {
       if (this.runId_ && !this.findRun(this.runId_)) {
         this.runId_ = undefined;
       }
     }
   }
 };
</script>

<style>
 .tabs__bar {
   padding: 0 16px !important;
 }
</style>
