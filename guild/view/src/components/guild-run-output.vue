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
        :headers="headers"
        :items="rows"
        :search="filter"
        item-key="index"
        :hide-headers="rows.length == 0"
        hide-actions
        must-sort
        no-data-text="There is no output associated with this run"
        no-results-text="No matches for the current filter">
        <template slot="items" slot-scope="rows">
          <tr :class="'stream-' + rows.item.stream">
            <td class="time">{{ formatTime(rows.item.time) }}</td>
            <td class="val">{{ rows.item.value }}</td>
          </tr>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script>
export default {
  name: 'guild-run-output',

  props: {
    run: {
      type: Object,
      required: true
    }
  },

  data() {
    return {
      filter: '',
      headers: [
        { text: 'Time', align: 'left', value: 'time', sortable: true },
        { text: '', align: 'left', value: 'value', sortable: false }
      ]
    };
  },

  computed: {
    rows() {
      return [
        { time: 1524579305106, value: 'This is line 0 of output yo!', stream: 1 },
        { time: 1524579308106, value: 'This is line 1 of output yo!', stream: 0 },
        { time: 1524579312106, value: 'This is line 2 of output yo!', stream: 1 },
        { time: 1524579320106, value: 'This is line 3 of output yo!', stream: 0 }
      ];
    }
  },

  methods: {
    formatTime(time) {
      const date = new Date(time);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
  }
};
</script>

<style scoped>
table td.time {
  white-space: nowrap;
}

table td.val {
  width: 99%;
}

table tr.stream-1 td {
  /* color: #B71C1C; */
  background-color: #FFEBEE;
  color: rgba(0, 0, 0, 0.67);
}
</style>
