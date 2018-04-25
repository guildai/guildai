<template>
  <div id="root" ref="content">
    <img :src="src" @load="onLoaded">
  </div>
</template>

<script>
import panzoom from 'panzoom';

export default {
  name: 'guild-image-viewer',

  props: {
    src: String
  },

  data() {
    return {
      pz: undefined
    };
  },

  mounted() {
    this.reset();
  },

  methods: {
    onLoaded(e) {
      const img = e.target;
      const dims = img.naturalWidth + ' x ' + img.naturalHeight;
      this.$emit('meta', [dims]);
    },

    reset() {
      this.$refs.content.removeAttribute('style');
      if (this.pz) {
        this.pz.dispose();
        this.pz = undefined;
      }
      const opts = {
        maxZoom: 5.0,
        minZoom: 1.0,
        smoothScroll: false
      };
      this.pz = panzoom(this.$refs.content, opts);
    }
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
