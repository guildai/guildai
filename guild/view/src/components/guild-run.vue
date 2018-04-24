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
        <v-tabs-item key="model" href="#model" ripple>
          Model
        </v-tabs-item>
        <v-tabs-item key="files" href="#files" ripple>
          Files
        </v-tabs-item>
        <v-tabs-item key="output" href="#output" ripple>
          Output
        </v-tabs-item>
        <v-tabs-slider color="deep-orange"></v-tabs-slider>
      </v-tabs-bar>
      <v-divider/>
    </div>
    <v-tabs-items>
      <v-tabs-content key="overview" id="overview">
        <guild-run-overview :run="run" />
      </v-tabs-content>
      <v-tabs-content key="model" id="model">
        <guild-run-model :run="run" />
      </v-tabs-content>
      <v-tabs-content key="files" id="files">
        <guild-run-files :run="run" />
      </v-tabs-content>
      <v-tabs-content key="output" id="output">
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
