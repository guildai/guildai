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
