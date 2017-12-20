<template>
  <v-container fluid grid-list-lg>
    <v-card>
      <v-card-title class="py-0">
        <v-spacer />
        <v-text-field
          append-icon="search"
          label="Filter"
          single-line
          hide-details
          clearable
          v-model="filter"
          style="max-width:20em" />
      </v-card-title>
      <v-data-table
        class="files"
        :headers="fileHeaders"
        :items="run.files"
        :search="filter"
        item-key="path"
        :hide-headers="run.files.length == 0"
        hide-actions
        must-sort
        no-data-text="There are no files associated with this run"
        no-results-text="No matches for the current filter">
        <template slot="items" slot-scope="files">
          <td class="type-icon">
            <v-tooltip left transition="fade-transition">
              <v-icon slot="activator">mdi-{{ files.item.icon }}</v-icon>
              <span>{{ files.item.iconTooltip }}</span>
            </v-tooltip>
          </td>
          <td v-if="files.item.viewer">
            <v-btn
              class="grey lighten-4 btn-link"
              flat small block
              style="margin-left: -8px"
              @click="viewerOpen = true">{{ files.item.path }}</v-btn></div>
          </td>
          <td v-else>{{ files.item.path }}</td>
          <td>{{ files.item.type }}</td>
          <td class="text-xs-right">{{ formatFileSize(files.item.size) }}</td>
        </template>
      </v-data-table>

    </v-card>

    <v-layout>
      <v-dialog
        ref="viewer"
        v-model="viewerOpen"
        scrollable
        :fullscreen="viewerFullscreen">
        <v-card style="height:640px">
          <v-card-title style="padding: 8px 4px 8px 16px">
            <v-select
              :items="media"
              v-model="viewerItem"
              return-object
              item-text="value"
              single-line
              :prepend-icon="viewerItem.icon" />
            <v-btn v-if="!viewerFullscreen" icon flat @click="viewerFullscreen = true"><v-icon>mdi-fullscreen</v-icon></v-btn>
            <v-btn v-if="viewerFullscreen" icon flat @click="viewerFullscreen = false"><v-icon>mdi-fullscreen-exit</v-icon></v-btn>
            <v-btn icon flat @click="viewerOpen = false"><v-icon>clear</v-icon></v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="viewer-content">
            <img :src="viewerItem.src">
          </v-card-text>
          <v-divider></v-divider>
          <v-card-actions>
            <v-btn flat @click="viewerNav(-1)">Prev</v-btn>
            <v-spacer />
            <v-btn flat @click="viewerNav(1)">Next</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-layout>

  </v-container>
</template>

<script>
 import filesize from 'filesize';

 export default {
   name: 'guild-run-files',

   props: {
     run: {
       type: Object,
       required: true
     }
   },

   data() {
     return {
       fileHeaders: [
         { text: '', value: '', sortable: false, width: 42 },
         { text: 'Name', value: 'path', align: 'left' },
         { text: 'Type', value: 'type', align: 'left' },
         { text: 'Size', value: 'size', align: 'right' }
       ],
       filter: '',
       viewerOpen: false,
       viewerItem_: undefined,
       viewerFullscreen: false,
       media: [
         { value: '2017-12-06_120417_01.mid', icon: 'mdi-file-music', src: 'https://maxpull-tlu7l6lqiu.stackpathdns.com/wp-content/uploads/2008/07/tulips-in-bloom.jpg' },
         { value: '2017-12-06_120417_02.mid', icon: 'mdi-file-music', src: 'https://www.almanac.com/sites/default/files/users/Almanac%20Staff/yellow-tulips_full_width.jpg' },
         { value: '2017-12-06_120417_03.mid', icon: 'mdi-file-image', src: 'https://cdn.shopify.com/s/files/1/1902/7917/products/Tulip-Jumbo-Darwin-Mix_330x415_crop_center.jpg' }
       ]
     };
   },

   computed: {
     viewerItem: {
       get() {
         if (this.viewerItem_) {
           return this.viewerItem_;
         } else if (this.media.length > 0) {
           return this.media[0];
         } else {
           return undefined;
         }
       },
       set(val) {
         this.viewerItem_ = val;
       }
     },

     viewerItemIndex() {
       for (var i = 0; i < this.media.length; i++) {
         if (this.media[i] === this.viewerItem) {
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
     formatFileSize(x) {
       return x != null ? filesize(x) : '';
     },

     handleKeyDown(e) {
       var selectOpen = document.getElementsByClassName(
         'menuable__content__active').length > 0;
       if (!this.viewerOpen || selectOpen) {
         return;
       }
       if (e.keyCode === 27) { // Esc
         this.viewerOpen = false;
       } else if (e.keyCode === 37) { // Left
         this.viewerNav(-1);
       } else if (e.keyCode === 39) { // Right
         this.viewerNav(1);
       }
     },

     viewerNav(incr) {
       var nextIndex = maybeWrapIndex(this.viewerItemIndex + incr, this.media);
       this.viewerItem = this.media[nextIndex];
     }
   }
 };

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
 .files table.table thead tr {
   height: 48px;
 }

 .btn-link {
   text-transform: inherit;
 }

 .btn-link .btn__content {
   justify-content: start;
 }

 .input-group__prepend-icon {
   min-width: 32px !important;
 }

 .input-group__details {
   max-width: calc(100% - 32px) !important;
   min-height: 16px !important;
 }
</style>

<style scoped>
 /* Use negative margin rather than padding to preserve spacing of
    input placeholder text. */
 .input-group {
   margin-top: -4px;
   margin-right: 16px;
 }

 td.type-icon {
   padding-right: 0 !important;
 }

 .viewer-title {
   display: flex;
 }

 .viewer-content {
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
   background-color: #666;
   height: 100%;
 }

 .viewer-content img {
   max-width: 100%;
   max-height: 100%;
 }
</style>
