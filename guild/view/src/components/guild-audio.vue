<template>
  <div id="root" class="grey lighten-2 pa-3 elevation-3">
    <v-btn :disabled="!paused" icon ripple size="400" @click="play(true)">
      <v-icon>mdi-play</v-icon>
    </v-btn>
    <v-btn :disabled="paused" icon ripple @click="play(false)">
      <v-icon>mdi-pause</v-icon>
    </v-btn>
    <v-progress-linear
      id="progress"
      v-model="progress"
      :indeterminate="progress < 0"
      class="mx-3" />
  </div>
</template>

<script>
 import MIDI from 'midi.js';

 export default {
   name: 'guild-audio',

   props: {
     src: { type: String }
   },

   data() {
     return {
       paused: true,
       progress: 0
     };
   },

   created() {
     console.log(MIDI);
   },

   methods: {
     play(flag) {
       this.paused = !flag;
       this.progress = flag ? -1 : 0;
     }
   }
 };
</script>

<style scoped>
 #root {
   display: flex;
   align-items: center;
 }

 #progress {
   width: 300px;
 }
</style>
