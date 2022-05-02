/* Copyright 2017-2022 RStudio, PBC
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
  <guild-text-loader :src="src" @input="text = $event">
    <div v-if="parsed.errors.length > 0" class="fallback">
      <p>
        An error occurred parsing table data. The unparsed data is
        displayed below.
      </p>
      <textarea readonly class="elevation-3 pa-3 white" >{{ text }}</textarea>
    </div>
    <v-data-table
      v-else
      :headers="data.headers"
      :items="data.items"
      hide-actions
      class="elevation-1 items">
      <template slot="items" slot-scope="rows">
        <td v-for="header in data.headers">
          {{ rows.item[header.value] }}
        </td>
      </template>
    </v-data-table>
  </guild-text-loader>
</template>

<script>
import Papa from 'papaparse';

export default {
  name: 'guild-table-viewer',

  props: {
    src: String
  },

  data() {
    return {
      text: ''
    };
  },

  computed: {
    parsed() {
      const text = this.text.trim();
      if (text === '') {
        // Papa doesn't handle empty strings without an explicit
        // delimiter.
        return Papa.parse('', {delimiter: ',', header: true});
      }
      const config = {
        delimiter: '',
        newline: '',
        header: true
      };
      const parsed = Papa.parse(text, config);
      if (parsed.errors.length > 0) {
        console.warn('errors parsing table text', parsed.errors);
      }
      return parsed;
    },

    data() {
      return {
        headers: this.parsed.meta.fields.map(name => ({
          text: name,
          align: 'left',
          sortable: true,
          value: name
        })),
        items: this.parsed.data
      };
    }
  }
};
</script>

<style>
.items table.table {
  width: unset;
}

@media (min-width: 600px) {
  .items table.table {
    min-width: 600px;
  }
}

</style>

<style scoped>
.fallback {
  display: flex;
  flex-direction: column;
  flex: 1;
  align-items: center;
}

.fallback p {
  color: #eee;
}

.fallback textarea {
  overflow: auto;
  flex: 1;
  resize: none;
  font-family: monospace;
}

.fallback textarea:focus {
  outline: none;
}

.items {
  width: unset;
}
</style>
