<template>
  <v-container fluid>
    <h1 class="mb-2">Compare runs</h1>
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
        class="compare-runs"
        :headers="headers"
        :items="runs"
        :pagination.sync="pagination"
        :search="filter"
        item-key="id"
        hide-actions
        must-sort
        no-data-text="There are currently no runs to compare"
        no-results-text="No matches for the current filter">
        <template slot="items" slot-scope="runs">
          <td class="nowrap">
            <v-tooltip
              top transition="fade-transition"
              tag="div">
              <!-- padding for link is to stave off tooltip -->
              <a slot="activator"
                 href="javascript:void(0)"
                 style="padding: 4px 0"
                 @click.prevent="$emit('run-selected', runs.item)"
              >{{ runs.item.operation }}</a>
              <span>[{{ runs.item.shortId }}] {{ runs.item.operation }}</span>
            </v-tooltip>
          </td>
          <td class="nowrap">{{ runs.item.started }}</td>
          <td>{{ runs.item.time }}</td>
          <td>{{ runs.item.status }}</td>
          <td>{{ runs.item.label }}</td>
          <td v-for="header in scalarHeaders">
            {{ fmtScalar(runs.item.scalars[header.value.substr(8)]) }}
          </td>
          <td v-for="header in flagHeaders">
            {{ runs.item.flags[header.value.substr(6)] }}
          </td>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script>
export default {

  name: 'guild-compare',

  props: {
    runs: {
      type: Array,
      required: true
    }
  },

  data() {
    return {
      filter: '',
      pagination: {
        sortBy: 'started',
        descending: true,
        rowsPerPage: -1
      }
    };
  },

  computed: {
    headers() {
      return [].concat(
        [
          {text: 'Run', value: 'operation', align: 'left'},
          {text: 'Started', value: 'started', align: 'left'},
          {text: 'Time', value: 'time', align: 'left'},
          {text: 'Status', value: 'status', align: 'left'},
          {text: 'Label', value: 'label', align: 'left'}
        ],
        this.scalarHeaders,
        this.flagHeaders);
    },

    scalarHeaders() {
      return [
        {text: 'Step', value: 'scalars.step', align: 'left'},
        {text: 'Accuracy', value: 'scalars.val_acc', align: 'left'},
        {text: 'Loss', value: 'scalars.loss', align: 'left'}
      ];
    },

    flagHeaders() {
      const flags = [];
      this.runs.forEach(run => {
        Object.keys(run.flags).forEach(flag => {
          if (!flags.includes(flag)) {
            flags.push(flag);
          }
        });
      });
      flags.sort();
      return flags.map(flag => ({
        text: flag,
        value: 'flags.' + flag,
        align: 'left'
      }));
    }
  },

  methods: {
    fmtScalar(n) {
      if (Number.isInteger(n)) {
        return n;
      } else if (n) {
        return n.toPrecision(4);
      } else {
        return n;
      }
    }
  }
};
</script>

<style>
.compare-runs > table.table thead th {
  font-size: 13px;
  outline: none !important;
}

.compare-runs > table.table thead th i {
  margin-left: 4px;
  color: #777 !important;
}

.compare-runs table.table tbody td {
  font-size: 14px;
}

.compare-runs table.table tbody td.nowrap {
  white-space: nowrap;
}

.compare-runs > table.table thead tr {
  height: 48px;
}
</style>
