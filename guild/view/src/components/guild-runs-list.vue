<template>
  <v-list>
    <v-subheader>
      <div>Runs</div>
      <v-spacer />
      <v-tooltip right transition="fade-transition">
        <v-btn
          flat small
          slot="activator"
          @click="tensorboard">
          &ensp;View in TensorBoard
        </v-btn>
        <span>View in TensorBoard</span>
      </v-tooltip>
    </v-subheader>
    <v-list-tile>
      <div style="width:100%; margin-top:-24px">
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
       return this.runs.filter(
         run => run.operation.toLowerCase().indexOf(filter) !== -1);
     }
   },

   methods: {
     runSelected(run) {
       this.$emit('input', run);
     },

     tensorboard() {
       console.log('TODO: open TensorBoard in another tab');
     }
   }
 };
</script>

<style>
 .list__tile {
   height: inherit;
   padding: 10px 16px;
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
</style>
