<template>
  <v-list>
    <v-subheader>Runs</v-subheader>
    <div class="runs-view-in-tensorboard">
      <v-btn
        flat small
        color="primary"
        @click="tensorboard">
        <v-icon>timeline</v-icon>
        &ensp;View in TensorBoard
      </v-btn>
    </div>
    <v-list-tile>
      <div style="width:100%; margin-top:-18px">
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
    <template v-for="run in filtered">
      <v-list-tile
        :key="run.id"
        @click="runSelected(run)"
        :class="{selected: value.id === run.id}"
        ripple>
        <v-list-tile-content>
          <v-tooltip
            top transition="fade-transition"
            tag="div"
            class="rev-ellipsis-container">
            <v-list-tile-title slot="activator" class="rev-ellipsis">
              &lrm;{{ run.operation }}
              <span v-if="run.label" class="run-title-label">{{ run.label }}</span>
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
   name: 'guild-runs-list',

   props: {
     runs: { type: Array, required: true },
     value: { type: Object }
   },

   data() {
     return {
       filter: ''
     };
   },

   computed: {
     filtered() {
       if (!this.filter) {
         return this.runs;
       }
       const filter = this.filter.toLowerCase();
       return this.runs.filter(run => {
         const text = (
           run.operation.toLowerCase()
           + run.label.toLowerCase()
           + run.id);
         return text.indexOf(filter) !== -1;
       });
     }
   },

   methods: {
     runSelected(run) {
       this.$emit('input', run);
     },

     tensorboard() {
       const qs = window.location.search;
       window.open(
         process.env.VIEW_BASE + '/tensorboard' + qs,
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
