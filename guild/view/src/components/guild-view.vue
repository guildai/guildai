<template>
  <v-app >
    <v-navigation-drawer
      app fixed clipped
      v-model="drawer"
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
            <v-tabs-item key="overview" href="overview" ripple>
              Overview
            </v-tabs-item>
            <v-tabs-item key="files" href="files" ripple>
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
        <p>There are no runs to view.</p>
      </v-container>
    </v-content>
    <v-footer fixed app color="grey lighten-2">
      <v-layout column justify-center style="margin:0">
        <v-divider />
        <v-layout align-center class="px-2 caption" style="height:36px">
          <div>{{ cwd }}</div>
        </v-layout>
      </v-layout>
    </v-footer>
  </v-app>
</template>

<script>
 import { formatRuns } from './guild-runs.js';
 import { SampleRuns, Cwd } from './sample-data.js';

 var drawerBreakPoint = 960;

 export default {
   name: 'guild-view',

   data() {
     return {
       drawerBreakPoint: drawerBreakPoint,
       drawer: window.innerWidth >= drawerBreakPoint,
       run_: undefined,
       runs: formatRuns(SampleRuns),
       cwd: Cwd,
       selectedTab: 'overview'
     };
   },

   computed: {
     run: {
       get() {
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
     }
   },

   methods: {

     runSelected(run) {
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
