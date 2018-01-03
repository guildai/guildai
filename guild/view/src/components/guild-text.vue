<template>
  <div id="root">
    <div
      id="loading"
      v-show="loading"
      class="elevation-3 pa-3 grey darken-3 white--text">
      <span class="mr-3">Reading file</span>
       <v-progress-circular indeterminate color="white" size="18" />
    </div>
    <textarea
      id="content"
      readonly
      v-show="!loading"
      ref="content"
      class="elevation-3 pa-3 grey darken-3 white--text" />
  </div>
</template>

<script>
 export default {
   name: 'guild-text',

   props: {
     src: { type: String }
   },

   data() {
     return {
       loading: false
     };
   },

   mounted() {
     console.log('refreshing 0 (mounted)');
     this.refresh();
     console.log('refreshing 1 (mounted)');
   },

   watch: {
     src() {
       console.log('refreshing 0 (src)');
       this.refresh();
       console.log('refreshing 1 (src)');
     }
   },

   methods: {
     refresh() {
       this.clear();
       const showLoading = this.scheduleLoading(100);
       this.scheduleFetch(0, showLoading);
     },

     clear() {
       this.$refs.content.value = '';
     },

     scheduleLoading(timeout) {
       const this_ = this;
       return setTimeout(() => {
         this_.loading = true;
       }, timeout);
     },

     scheduleFetch(timeout, showLoading) {
       const this_ = this;
       setTimeout(() => {
         fetch(this_.src).then(function (resp) {
           return resp.text();
         }).then(function (text) {
           this_.$refs.content.value = text;
           clearTimeout(showLoading);
           this_.loading = false;
         });
       }, timeout);
     }
   }
 };
</script>

<style scoped>
 #root {
   height: 100%;
   width: 100%;
 }

 #loading {
   height: 100%;
   width: 100%;
   display: flex;
   align-items: center;
   justify-content: center;
 }

 #content {
   overflow: auto;
   height: 100%;
   width: 100%;
   resize: none;
   font-family: monospace;
 }

 #content:focus {
   outline: none;
 }
</style>
