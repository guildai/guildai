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
    <div class="mt-1 grey--text text--darken-2">{{ run.path }}</div>
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
