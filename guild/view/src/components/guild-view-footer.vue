<template>
  <v-footer fixed app color="grey lighten-2">
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
     config: Object
   }
};
</script>
