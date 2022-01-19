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
  <v-tooltip
    :top="tooltipTop"
    :left="tooltipLeft"
    :bottom="tooltipBottom"
    :right="tooltipRight"
    transition="fade-transition">
    <v-progress-circular
      v-if="icon.spinner"
      indeterminate
      :color="icon.color"
      :size="spinnerSize"
      slot="activator" />
    <v-icon
      v-else
      :color="icon.color"
      :medium="medium"
      :large="large"
      :x-large="xLarge"
      slot="activator">mdi-{{ icon.icon }}</v-icon>
    <span>{{ icon.tooltip }}</span>
  </v-tooltip>
</template>

<script>
export default {
  name: 'guild-run-status-icon',

  props: {
    icon: {
      type: Object,
      required: true
    },
    medium: Boolean,
    large: Boolean,
    xLarge: Boolean,
    tooltipTop: Boolean,
    tooltipLeft: Boolean,
    tooltipBottom: Boolean,
    tooltipRight: Boolean
  },

  computed: {
    spinnerSize() {
      if (this.medium) {
        return 28;
      } else if (this.large) {
        return 35;
      } else if (this.xLarge) {
        return 42;
      } else {
        return 24;
      }
    }
  }
};
</script>
