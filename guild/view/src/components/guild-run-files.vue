/* Copyright 2017-2023 Posit Software, PBC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
          style="max-width:20em;margin-bottom:-8px" />
      </v-card-title>
      <v-data-table
        ref="table"
        :headers="fileHeaders"
        :items="run.files"
        :search="filter"
        item-key="path"
        :hide-headers="run.files.length == 0"
        hide-actions
        disable-initial-sort
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
            <span class="no-wrap">{{ formatFileSize(files.item.size) }}</span>
          </td>
          <td>
            <span class="no-wrap">{{ formatTime(files.item.mtime) }}</span>
          </td>
        </template>
      </v-data-table>
    </v-card>
    <guild-files-viewer
      :files="viewable"
      :path="viewing ? viewing.path : undefined"
      :src-base="runSrcBase"
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
        { text: 'Size', value: 'size', align: 'right' },
        { text: 'Modified', value: 'mtime', align: 'left' }
      ],
      filter: '',
      viewing: undefined,
      viewerOpen: false
    };
  },

  computed: {
    runSrcBase() {
      return process.env.VIEW_BASE + '/files/' + this.run.id + '/';
    },

    filtered() {
      if (this.filter !== '' && this.$refs.table !== undefined) {
        return this.$refs.table.filteredItems;
      } else {
        return this.run.files;
      }
    },

    viewable() {
      return this.filtered.filter(file => file.viewer);
    }
  },

  methods: {
    formatFileSize(n) {
      return n !== null ? filesize(n) : '';
    },

    formatTime(mtime) {
      if (mtime !== null) {
        const date = new Date(mtime);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
      } else {
        return '';
      }
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
  height: unset;
  padding: 4px 0;
  display: block;
  text-align: left;
}

.path {
  word-break: break-all;
}

.no-wrap {
  white-space: nowrap;
}
</style>
