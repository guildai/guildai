<template>
  <div>
    <div class="right mt-3">
      <v-tooltip left transition="fade-transition">
        <v-icon
          large
          :color="run.icon.color"
          slot="activator">mdi-{{ run.icon.icon }}</v-icon>
        <span>{{ run.icon.tooltip }}</span>
      </v-tooltip>
    </div>
    <v-tooltip top transition="fade-transition" style="display:inline-block">
      <h1 slot="activator">{{ run.operation }}</h1>
      <span>[{{ run.shortId }}] {{ run.operation }}</span>
    </v-tooltip>
    <div>{{ run.started }}</div>
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
