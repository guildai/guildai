/* Copyright 2017-2022 RStudio, PBC
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
  <div id="root">
    <div
      id="loading"
      v-if="loading"
      class="elevation-3 pa-3 grey darken-3 white--text">
      <span class="mr-3">Reading file</span>
      <v-progress-circular indeterminate color="white" size="18" />
    </div>
    <slot v-else></slot>
  </div>
</template>

<script>
export default {
  name: 'guild-text-loader',

  props: {
    src: String
  },

  data() {
    return {
      loading: false
    };
  },

  mounted() {
    this.refresh();
  },

  watch: {
    src() {
      this.refresh();
    }
  },

  methods: {
    refresh() {
      this.clear();
      const showLoading = this.scheduleLoading(100);
      this.scheduleFetch(0, showLoading);
    },

    clear() {
      this.$emit('input', '');
    },

    scheduleLoading(timeout) {
      const this_ = this;
      return setTimeout(() => {
        this_.loading = true;
      }, timeout);
    },

    scheduleFetch(timeout, showLoading) {
      const this_ = this;
      setTimeout(() => {
        fetch(this_.src).then(function(resp) {
          return resp.text();
        }).then(function(text) {
          this_.$emit('input', text);
          clearTimeout(showLoading);
          this_.loading = false;
        });
      }, timeout);
    }
  }
};
</script>

<style scoped>
#root {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  justify-content: center;
  align-items: center;
}

#loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
