<template>
  <v-list>
    <v-subheader>Runs</v-subheader>
    <v-divider />
    <template v-for="run in runs">
      <v-list-tile
        :key="run.id"
        @click="runSelected(run)"
        :class="{selected: value === run}"
        ripple>
        <v-list-tile-content>
          <v-tooltip top transition="fade-transition" tag="div" style="width:100%">
            <v-list-tile-title slot="activator" class="rev-ellipsis">
              &lrm;{{ run.operation }}
            </v-list-tile-title>
            <span>[{{ run.shortId }}] {{ run.operation }}</span>
          </v-tooltip>
          <v-list-tile-sub-title>{{ run.started }}</v-list-tile-sub-title>
        </v-list-tile-content>
        <v-list-tile-action style="min-width: 28px">
          <v-tooltip right transition="fade-transition">
            <v-icon
              :color="run.icon.color"
              slot="activator">mdi-{{ run.icon.icon }}</v-icon>
            <span>{{ run.icon.tooltip }}</span>
          </v-tooltip>
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

   methods: {
     runSelected(run) {
       this.$emit('input', run);
     }
   }
 };
</script>

<style>
 .list__tile {
   height: inherit;
   padding: 10px 16px;
 }

 .rev-ellipsis {
   direction: rtl;
 }

 li.selected {
   background-color: #f5f5f5;
 }
</style>
