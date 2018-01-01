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
          <tr>
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
            <td>
              <a
                v-if="files.item.run"
                :href="'?run=' + files.item.run + '#files'"
                target="_blank">{{ files.item.operation }}</a>
            </td>
            <td class="text-xs-right">{{ formatFileSize(files.item.size) }}</td>
          </tr>
        </template>
      </v-data-table>
    </v-card>
    <guild-files-viewer :files="media" v-model="viewerOpen" />
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
         { text: 'Source operation', value: 'operation', align: 'left' },
         { text: 'Size', value: 'size', align: 'right' }
       ],
       filter: '',
       viewerOpen: false,
       media: [
         { value: '2017-12-06_120417_01.mid', icon: 'mdi-file-music', src: 'https://maxpull-tlu7l6lqiu.stackpathdns.com/wp-content/uploads/2008/07/tulips-in-bloom.jpg' },
         { value: '2017-12-06_120417_02.mid', icon: 'mdi-file-music', src: 'https://www.almanac.com/sites/default/files/users/Almanac%20Staff/yellow-tulips_full_width.jpg' },
         { value: '2017-12-06_120417_03.mid', icon: 'mdi-file-image', src: 'https://cdn.shopify.com/s/files/1/1902/7917/products/Tulip-Jumbo-Darwin-Mix_330x415_crop_center.jpg' }
       ]
     };
   },

   methods: {
     formatFileSize(x) {
       return x != null ? filesize(x) : '';
     }
   }
 };
</script>

<style>
 .files table.table thead tr {
   height: 48px;
 }

 .files table.table thead th {
   white-space: inherit;
 }

 .btn-link {
   text-transform: inherit;
   font-weight: 400;
 }

 .btn-link .btn__content {
   justify-content: start;
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
</style>
