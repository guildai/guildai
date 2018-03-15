<template>
  <v-toolbar fixed app clipped-left class="indigo darken-1 white--text">
    <v-toolbar-side-icon class="white--text" @click="drawerClick"></v-toolbar-side-icon>
    <v-toolbar-title v-text="title"></v-toolbar-title>
    <v-spacer></v-spacer>
  </v-toolbar>
</template>

<script>
export default {
  name: 'guild-view-toolbar',

  props: {
    title: {
      type: String,
      default: 'Guild View'
    }
  },

  methods: {
    drawerClick() {
      this.$emit('drawer-click');
    }
  }
};
</script>

<style scoped>
div.toolbar__title {
  margin-left: 6px;
}
</style>
