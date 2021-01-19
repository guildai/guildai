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
  <v-footer :fixed="fixed" app color="grey lighten-2">
    <v-layout column justify-center style="margin:0">
      <v-divider />
      <v-layout align-center class="px-2 caption" style="height:36px">
        <div>{{ config.cwd }}</div>
        <v-spacer />
        <div v-show="config.version">Guild AI v{{ config.version }}</div>
      </v-layout>
    </v-layout>
  </v-footer>
</template>

<script>
export default {
  name: 'guild-view-footer',

  props: {
    config: Object,
    fixed: {
      type: Boolean,
      default: true
    }
  }
};
</script>
