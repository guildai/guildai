/* Copyright 2017-2022 TensorHub, Inc.
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
        <v-tabs-item key="output" href="#log" ripple>
          Log
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
      <v-tabs-content key="log" id="log">
        <guild-run-output :run="run" />
      </v-tabs-content>
    </v-tabs-items>
  </v-tabs>
</template>

<script>
export default {
  name: 'guild-run',

  props: {
    run: Object
  },

  data() {
    return {
      selectedTab_: undefined
    };
  },

  computed: {
    selectedTab: {
      get() {
        if (this.selectedTab_) {
          return this.selectedTab_;
        } else if (window.location.hash) {
          return window.location.hash.substr(1);
        } else {
          return 'overview';
        }
      },
      set(val) {
        this.selectedTab_ = val;
      }
    }
  },

  watch: {
    '$route'() {
      // Use vue router to detect changes in hash - we handle this manually
      // to avoid the complexity of vue router with the tab control.
      var tab = window.location.hash
              ? window.location.hash.substr(1)
              : 'overview';
      this.selectedTab = tab;
    },

    selectedTab(val) {
      var hash = val === 'overview' ? '' : val;
      window.location.replace('#' + hash);
    }
  }
};
</script>

<style>
</style>
