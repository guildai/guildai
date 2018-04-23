<template>
  <div>
    <img ref="img" :src="src">
  </div>
</template>

<script>
import './imageviewer.css';
import './imageviewer.js';

export default {
  name: 'guild-image-viewer',

  props: {
    src: String
  },

  data() {
    return {
      viewer: undefined
    };
  },

  mounted() {
    const img = $(this.$refs.img);
    img.ImageViewer();
    this.viewer = img.data('ImageViewer');
  },

  beforeDestroy() {
    if (this.viewer) {
      this.viewer.destroy();
    }
  }
};
</script>

<style scoped>
</style>
