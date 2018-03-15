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
      <guild-view-waiting v-else />
    </v-content>
    <guild-view-footer :config="config" />
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
     },

     drawer(val) {
       console.log('DRAWER CHANGED');
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

     findRun(id) {
       return this.runs.find(run => run.id === id);
     },

     checkRunDeleted() {
       if (this.runId_ && !this.findRun(this.runId_)) {
         this.runId_ = undefined;
       }
     },

     maybeCloseDrawer() {
       if (window.innerWidth < drawerBreakPoint) {
         this.drawer = false;
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
