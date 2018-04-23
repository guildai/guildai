<template>
  <guild-text-loader :src="src" @input="text = $event">
    <div v-if="parsed.errors.length > 0" class="fallback">
      <p>An error occurred parsing table data. The unparsed data is displayed below.</p>
      <textarea readonly class="elevation-3 pa-3 white" >{{ text }}</textarea>
    </div>
    <v-data-table
      v-else
      :headers="data.headers"
      :items="data.items"
      hide-actions
      class="elevation-1">
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

<style scoped>
.fallback {
  display: flex;
  flex-direction: column;
  flex: 1;
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
</style>
