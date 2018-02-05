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
                @click="view(files.item)">{{ files.item.path }}</v-btn></div>
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
    <guild-files-viewer
      :files="media"
      :path="curMedia ? curMedia.path : undefined"
      v-model="viewerOpen" />
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
         { text: 'Source', value: 'operation', align: 'left' },
         { text: 'Size', value: 'size', align: 'right' }
       ],
       filter: '',
       curMedia: undefined,
       viewerOpen: false
     };
   },

   computed: {
     media() {
       var filtered = this.run.files.filter(file => file.viewer);
       return filtered.map(file => {
         return {
           path: file.path,
           icon: 'mdi-' + file.icon,
           viewer: file.viewer,
           src: process.env.VIEW_BASE + '/runs/' + this.run.id + '/' + file.path
         };
       });
     }
   },

   methods: {
     formatFileSize(x) {
       return x != null ? filesize(x) : '';
     },

     view(file) {
       var mediaFile = this.media.find(mfile => mfile.path === file.path);
       this.curMedia = mediaFile;
       this.viewerOpen = true;
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
 }

 td.type-icon {
   padding-right: 0 !important;
 }
</style>
