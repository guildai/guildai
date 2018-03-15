<template>
  <v-list>
    <v-subheader>Runs</v-subheader>
    <v-list-tile>
      <div style="width:100%; margin-top:-24px; margin-bottom:-6px">
        <v-text-field
          v-model="filter"
          append-icon="search"
          label="Filter"
          single-line
          hide-details
          clearable
          style="font-weight:400"
        />
      </div>
    </v-list-tile>
    <v-divider />
    <v-list-tile ripple @click="tensorboard" class="tile-button">
      <v-list-tile-content>
        <v-tooltip top transition="fade-transition" tag="div" >
          <v-list-tile-title slot="activator">
            <v-icon style="margin-top:-3px">timeline</v-icon>
            View in TensorBoard
          </v-list-tile-title>
          <span>View runs in TensorBoard</span>
        </v-tooltip>
      </v-list-tile-content>
    </v-list-tile>
    <v-divider />
    <v-list-tile
      @click="select({compare: true})"
      :class="{selected: selected.compare}"
      ripple>
      <v-list-tile-content>
        <v-tooltip top transition="fade-transition" tag="div" >
          <v-list-tile-title slot="activator">
            <v-icon style="margin-top:-3px">mdi-sort</v-icon>
            Compare runs
          </v-list-tile-title>
          <span>Compare runs</span>
        </v-tooltip>
      </v-list-tile-content>
    </v-list-tile>
    <v-divider />
    <template v-for="run in filteredRuns">
      <v-list-tile
        :key="run.id"
        @click="select({run: run})"
        :class="{selected: selected.run && selected.run.id === run.id}"
        ripple>
        <v-list-tile-content>
          <v-tooltip
            top transition="fade-transition"
            tag="div"
            class="rev-ellipsis-container">
            <v-list-tile-title slot="activator" class="rev-ellipsis">
              &lrm;{{ run.operation }}
              <span v-if="run.label" class="run-title-label">
                {{ run.label }}
              </span>
            </v-list-tile-title>
            <span>[{{ run.shortId }}] {{ run.operation }}</span>
          </v-tooltip>
          <v-list-tile-sub-title>{{ run.started }}</v-list-tile-sub-title>
        </v-list-tile-content>
        <v-list-tile-action style="min-width: 28px">
          <guild-run-status-icon :icon="run.icon" tooltip-right />
        </v-list-tile-action>
      </v-list-tile>
      <v-divider />
    </template>
  </v-list>
</template>

<script>
export default {
  name: 'guild-view-select',

  props: {
    runs: {
      type: Array,
      required: true
    },
    value: {
      type: Object,
      default: undefined
    }
  },

  data() {
    return {
      filter: ''
    };
  },

  computed: {
    filteredRuns() {
      if (!this.filter) {
        return this.runs;
      }
      const filter = this.filter.toLowerCase();
      return this.runs.filter(run => {
        const text = (
          run.operation.toLowerCase() +
          run.label.toLowerCase() +
          run.id);
        return text.indexOf(filter) !== -1;
      });
    },

    selected() {
      var val = this.value || {};
      if (val.compare) {
        return val;
      } else {
        // Want to show a run
        var runs = this.filteredRuns;
        // If run specified, validate against runs
        if (val.run && runs.some(run => run.id === val.run.id)) {
          return val;
        }
        // No run or stale run selected, use first in list as default
        if (runs.length > 0) {
          return {run: runs[0]};
        }
        // Nothing selected
        return {};
      }
    }
  },

  watch: {
    selected(val) {
      if (val !== this.value) {
        this.$emit('input', val);
      }
    }
  },

  methods: {
    select(val) {
      this.$emit('input', val);
    },

    tensorboard() {
      const qs = window.location.search;
      window.open(
        process.env.VIEW_BASE + '/tb/' + qs,
        'guild-tb-' + qs);
    }
  }
};
</script>

<style>
.list__tile {
  height: inherit;
  padding: 10px 16px;
}

.run-title-label {
  color: rgba(0,0,0,0.54);
  margin-right: 10px;
  float: right;
}

.rev-ellipsis-container {
  width: 100%;
}

.rev-ellipsis {
  direction: rtl;
}

li.selected {
  background-color: #f5f5f5;
}

.runs-view-in-tensorboard {
  position: absolute;
  top: 12px;
  right: 0;
}
</style>
