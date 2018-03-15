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
          style="max-width:20em;margin-bottom:-12px" />
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
                class="grey lighten-3 btn-link"
                flat small block
                style="margin-left: -8px"
                @click="view(files.item)"><span class="path">{{ files.item.path }}</span></v-btn></div>
            </td>
            <td v-else><span class="path">{{ files.item.path }}</span></td>
            <td>{{ files.item.type }}</td>
            <td>
              <a
                v-if="files.item.run"
                :href="'?run=' + files.item.run + '#files'"
                target="_blank">{{ files.item.operation }}</a>
            </td>
            <td class="text-xs-right"><span class="file-size">{{ formatFileSize(files.item.size) }}</span></td>
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
.btn-link .btn__content {
  justify-content: start;
  white-space: normal;
}

.files > table.table thead th {
  font-size: 13px;
}

.files > table.table thead tr {
  height: 48px;
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

.btn-link {
  text-transform: none;
  width: inherit;
  font-size: 14px;
  height: unset;
  padding: 4px 0;
  display: block;
  text-align: left;
}

.files table.table thead tr {
  height: 48px;
}

.files table.table thead th {
  white-space: inherit;
}

.path {
  word-break: break-all;
}

table.table tbody td {
  font-size: 14px;
}

table.table thead th {
  font-size: 13px;
}

.file-size {
  white-space: nowrap;
}
</style>
