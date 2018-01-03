<template>
  <v-app >
    <v-navigation-drawer
      app fixed clipped
      v-model="drawer"
      width="360"
      :mobile-break-point="drawerBreakPoint">
      <guild-runs-list :runs="runs" v-model="run" @input="runSelected" />
    </v-navigation-drawer>
    <guild-view-toolbar @drawer-click="drawer = !drawer" />
    <v-content>
      <v-tabs v-if="run" v-model="selectedTab">
        <div class="grey lighten-4">
          <v-container fluid pl-4 pb-2>
            <guild-run-titlebar :run="run" />
          </v-container>
          <v-tabs-bar>
            <v-tabs-item key="overview" href="#overview" ripple>
              Overview
            </v-tabs-item>
            <v-tabs-item key="files" href="#files" ripple>
              Files
            </v-tabs-item>
            <v-tabs-slider color="deep-orange"></v-tabs-slider>
          </v-tabs-bar>
          <v-divider/>
        </div>
        <v-tabs-items>
          <v-tabs-content key="overview" id="overview">
            <guild-run-overview :run="run" />
          </v-tabs-content>
          <v-tabs-content key="files" id="files">
            <guild-run-files :run="run" />
          </v-tabs-content>
        </v-tabs-items>
      </v-tabs>
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
       selectedTab_: undefined,
       run_: undefined,
       runs: [],
       config: {}
     };
   },

   created() {
     this.initData();
   },

   computed: {
     selectedTab: {
       get() {
         if (this.selectedTab_) {
           return this.selectedTab_;
         } else if (this.$route.hash) {
           return this.$route.hash.substr(1);
         } else {
           return 'overview';
         }
       },
       set(val) {
         this.selectedTab_ = val;
       }
     },

     run: {
       get() {
         this.checkRunDeleted();
         if (this.run_) {
           return this.run_;
         } else if (this.runs) {
           return this.runs[0];
         } else {
           return undefined;
         }
       },
       set(val) {
         this.run_ = val;
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
     '$route'(route) {
       // This is handled manually (see also selectedTab watcher) to
       // avoid the complexity of using vue-router with v-tabs.
       var tab = route.hash ? route.hash.substr(1) : 'overview';
       this.selectedTab = tab;
     },

     selectedTab(val) {
       var hash = val === 'overview' ? '' : val;
       window.location.replace('#' + hash);
     },

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
       fetchData('/config', this.$route, function(config) {
         this_.config = config;
       });
     },

     fetchRuns() {
       var this_ = this;
       fetchData('/runs', this.$route, function(runs) {
         this_.runs = formatRuns(runs);
         this_.scheduleNextFetchRuns();
       });
     },

     scheduleNextFetchRuns() {
       setTimeout(this.fetchRuns, 5000);
     },

     runSelected(run) {
       if (window.innerWidth < drawerBreakPoint) {
         this.drawer = false;
       }
     },

     checkRunDeleted() {
       if (this.run_) {
         const match = this.runs.find((run) => run.id === this.run_.id);
         if (!match) {
           this.run_ = undefined;
         }
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
