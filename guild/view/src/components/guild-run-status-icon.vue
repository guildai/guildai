<template>
  <v-tooltip right transition="fade-transition">
    <v-icon
      :color="icon.color"
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
     }
   }
 };
</script>
