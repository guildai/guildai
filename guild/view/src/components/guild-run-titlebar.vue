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
  <div>
    <div class="right mt-3">
      <guild-run-status-icon :icon="run.icon" large tooltip-left />
    </div>
    <v-tooltip top transition="fade-transition" style="display:inline-block">
      <h1 slot="activator">{{ run.operation }}</h1>
      <span>[{{ run.shortId }}] {{ run.operation }}</span>
    </v-tooltip>
    <div>{{ run.started }}</div>
    <div class="mt-1 grey--text text--darken-2">{{ run.dir }}</div>
  </div>
</template>

<script>
export default {
  name: 'guild-run-titlebar',

  props: {
    run: {
      type: Object,
      required: true
    }
  }
};
</script>
