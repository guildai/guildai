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
  <guild-text-loader :src="src" @input="text = $event">
    <textarea readonly class="elevation-3 pa-3 white" >{{ text }}</textarea>
  </guild-text-loader>
</template>

<script>
export default {
  name: 'guild-text-viewer',

  props: {
    src: String
  },

  data() {
    return {
      text: ''
    };
  }
};
</script>

<style scoped>
textarea {
  overflow: auto;
  flex: 1;
  resize: none;
  font-family: monospace;
}

@media (min-width: 600px) {
  textarea {
    min-width: 600px;
  }
}

textarea:focus {
  outline: none;
}
</style>
