<template>
  <div id="root" ref="content">
    <img :src="src">
  </div>
</template>

<script>
import panzoom from 'panzoom';

export default {
  name: 'guild-image-viewer',

  props: {
    src: String
  },

  mounted() {
    const opts = {
      maxZoom: 5.0,
      minZoom: 1.0,
      smoothScroll: false
    };
    panzoom(this.$refs.content, opts);
  }
};
</script>

<style scoped>
#root {
  height: 100%;
}

img {
  max-height: 100%;
  max-width: 100%;
  display: block
}
</style>
