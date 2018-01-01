<template>
  <v-dialog
    ref="viewer"
    v-model="visible"
    scrollable
    :fullscreen="fullscreen">
    <v-card style="height:640px">
      <v-card-title style="padding: 8px 4px 8px 16px">
        <v-select
          :items="files"
          v-model="cur"
          return-object
          item-text="value"
          single-line
          :prepend-icon="cur.icon" />
        <v-btn
          v-if="!fullscreen"
          icon flat
          @click="fullscreen = true">
          <v-icon>mdi-fullscreen</v-icon>
        </v-btn>
        <v-btn
          v-if="fullscreen"
          icon flat @click="fullscreen = false">
          <v-icon>mdi-fullscreen-exit</v-icon>
        </v-btn>
        <v-btn
          icon flat @click="visible = false">
          <v-icon>clear</v-icon>
        </v-btn>
      </v-card-title>
      <v-divider />
      <v-card-text class="content">
        <img :src="cur.src">
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions>
        <v-btn flat @click="nav(-1)">Prev</v-btn>
        <v-spacer />
        <v-btn flat @click="nav(1)">Next</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
 export default {
   name: 'guild-files-viewer',

   props: {
     files: {
       type: Array,
       required: true
     },
     value: { type: Boolean }
   },

   data() {
     return {
       cur_: undefined,
       fullscreen: false
     };
   },

   computed: {
     visible: {
       get() {
         return this.value;
       },
       set(val) {
         this.$emit('input', val);
       }
     },

     cur: {
       get() {
         if (this.cur_) {
           return this.cur_;
         } else if (this.files.length > 0) {
           return this.files[0];
         } else {
           return undefined;
         }
       },
       set(val) {
         this.cur_ = val;
       }
     },

     curIndex() {
       for (var i = 0; i < this.files.length; i++) {
         if (this.files[i] === this.cur) {
           return i;
         }
       }
       return -1;
     }
   },

   created() {
     window.addEventListener('keydown', this.handleKeyDown);
   },

   destroyed() {
     window.removeEventListener('keydown', this.handleKeyDown);
   },

   methods: {
     handleKeyDown(e) {
       if (!this.value || isMenuOpen()) {
         return;
       }
       if (e.keyCode === 27) { // Esc
         this.visible = false;
       } else if (e.keyCode === 37) { // Left
         this.nav(-1);
       } else if (e.keyCode === 39) { // Right
         this.nav(1);
       }
     },

     nav(incr) {
       var nextIndex = maybeWrapIndex(this.curIndex + incr, this.files);
       this.cur = this.files[nextIndex];
     }
   }
 };

 function isMenuOpen() {
   return document.getElementsByClassName(
     'menuable__content__active').length > 0;
 }

 function maybeWrapIndex(index, array) {
   if (index < 0) {
     return array.length - 1;
   } else if (index >= array.length) {
     return 0;
   } else {
     return index;
   }
 };
</script>

<style>
 .input-group__prepend-icon {
   min-width: 32px !important;
 }

 .input-group__details {
   max-width: calc(100% - 32px) !important;
   min-height: 16px !important;
 }
</style>

<style scoped>
 .input-group {
   padding-right: 16px;
 }

 .content {
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
   background-color: #666;
   height: 100%;
 }

 .content img {
   max-width: 100%;
   max-height: 100%;
 }
</style>
