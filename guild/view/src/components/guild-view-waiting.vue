<template>
  <v-container v-else>
    <v-layout row align-center>
      <span class="mr-3">Waiting for runs</span>
      <v-progress-circular indeterminate color="primary" size="18"/>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  name: 'guild-view-waiting'
};
</script>
