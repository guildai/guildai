/* Copyright 2017-2022 RStudio, PBC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

img {
  max-height: 100%;
  max-width: 100%;
  display: block
}
</style>
