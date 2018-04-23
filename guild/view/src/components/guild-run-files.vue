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
        ref="table"
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
              class="grey lighten-3 btn-link"
              flat small block
              style="margin-left: -8px"
              @click="view(files.item)">
              <span class="path">{{ files.item.path }}</span>
            </v-btn>
          </td>
          <td v-else><span class="path">{{ files.item.path }}</span></td>
          <td>{{ files.item.type }}</td>
          <td>
            <a
              v-if="files.item.run"
              :href="'?run=' + files.item.run + '#files'"
              target="_blank">{{ files.item.operation }}</a>
            <span v-else-if="files.item.operation">{{ files.item.operation }}</span>
          </td>
          <td class="text-xs-right">
            <span class="file-size">{{ formatFileSize(files.item.size) }}</span>
          </td>
        </template>
      </v-data-table>
    </v-card>
    <guild-files-viewer
      :files="viewable"
      :path="viewing ? viewing.path : undefined"
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
      viewing: undefined,
      viewerOpen: false
    };
  },

  computed: {
    filtered() {
      if (this.filter !== '' && this.$refs.table !== undefined) {
        return this.$refs.table.filteredItems;
      } else {
        return this.run.files;
      }
    },

    viewable() {
      const viewable = this.filtered.filter(file => file.viewer);
      return viewable.map(file => {
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
      const mediaFile = this.viewable.find(mfile => mfile.path === file.path);
      this.viewing = mediaFile;
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
  outline: none !important;
}

.files > table.table thead th i {
  margin-left: 4px;
  color: #777 !important;
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

.file-size {
  white-space: nowrap;
}
</style>
