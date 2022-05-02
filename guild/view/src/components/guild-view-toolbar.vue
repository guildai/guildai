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
  <v-toolbar fixed app clipped-left class="indigo darken-1 white--text">
    <v-toolbar-side-icon class="white--text" @click="drawerClick"></v-toolbar-side-icon>
    <v-toolbar-title v-text="title"></v-toolbar-title>
    <v-spacer></v-spacer>
  </v-toolbar>
</template>

<script>
export default {
  name: 'guild-view-toolbar',

  props: {
    title: {
      type: String,
      default: 'Guild View'
    }
  },

  methods: {
    drawerClick() {
      this.$emit('drawer-click');
    }
  }
};
</script>

<style scoped>
div.toolbar__title {
  margin-left: 6px;
}
</style>
