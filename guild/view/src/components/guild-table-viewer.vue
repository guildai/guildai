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
      console.log(this.parsed.meta, this.parsed.data);
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

  /*
      headers: [
        {
          text: 'Dessert (100g serving)',
          align: 'left',
          sortable: false,
          value: 'name'
        },
        { text: 'Calories', value: 'calories' },
        { text: 'Fat (g)', value: 'fat' },
        { text: 'Carbs (g)', value: 'carbs' },
        { text: 'Protein (g)', value: 'protein' },
        { text: 'Iron (%)', value: 'iron' }
      ],
      items: [
        {
          value: false,
          name: 'Frozen Yogurt',
          calories: 159,
          fat: 6.0,
          carbs: 24,
          protein: 4.0,
          iron: '1%'
        },
        {
          value: false,
          name: 'Ice cream sandwich',
          calories: 237,
          fat: 9.0,
          carbs: 37,
          protein: 4.3,
          iron: '1%'
        }
      ]
};
*/
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
