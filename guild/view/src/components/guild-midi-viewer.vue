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
  <div id="root" class="white pa-3 elevation-3">
    <v-btn icon ripple size="400" @click="togglePlay">
      <v-icon v-if="state !== 'playing'">mdi-play</v-icon>
      <v-icon v-else>mdi-pause</v-icon>
    </v-btn>
    <v-btn :disabled="state === 'stopped'" icon ripple @click="stop">
      <v-icon>mdi-stop</v-icon>
    </v-btn>
    <span :class="'ml-3 time ' + state">{{ curTime }}</span>
    <v-progress-linear
      v-show="progress > 0"
      v-model="progress"
      class="progress mx-3" />
    <v-progress-linear
      v-show="progress === 0"
      class="progress mx-3" />
    <span :class="'mr-3 time ' + state">{{ endTime }}</span>
  </div>
</template>

<script>
import MIDI from 'midi.js';

export default {
  name: 'guild-midi',

  props: {
    src: String,
    active: Boolean
  },

  data() {
    return {
      state: 'stopped',
      progress: 0,
      player: undefined,
      playerSrc: undefined,
      curTime: '00:00',
      endTime: '00:00'
    };
  },

  watch: {
    src() {
      this.reset();
    },

    active() {
      if (!this.active) {
        this.stop();
      }
    }
  },

  methods: {
    initPlayer() {
      const this_ = this;
      MIDI.loadPlugin({
        soundfontUrl: '/assets/soundfont/',
        onsuccess() {
          this_.player = MIDI.Player;
          this_.initPlayerSrc();
        }
      });
    },

    initPlayerSrc() {
      const this_ = this;
      fetch(this_.src).then(function(resp) {
        return resp.arrayBuffer();
      }).then(function(buf) {
        const data = String.fromCharCode.apply(null, new Uint8Array(buf));
        this_.player.currentData = data;
        this_.playerSrc = this_.src;
        this_.player.loadMidiFile(function() {
          this_.player.setAnimation(this_.playerProgress);
          this_.player.start();
        });
      });
    },

    togglePlay() {
      if (this.state === 'playing') {
        this.pause();
      } else {
        this.play();
      }
    },

    play() {
      const resume = this.state === 'paused';
      this.state = 'playing';
      if (!this.player) {
        this.initPlayer();
      } else if (this.playerSrc !== this.src) {
        this.initPlayerSrc();
      } else {
        this.player.setAnimation(this.playerProgress);
        if (resume) {
          this.player.resume();
        } else {
          this.player.start();
        }
      }
    },

    pause() {
      this.state = 'paused';
      if (this.player) {
        this.player.clearAnimation();
        this.player.pause(true);
      }
    },

    stop() {
      this.state = 'stopped';
      this.progress = 0;
      this.curTime = '00:00';
      if (this.player) {
        this.player.clearAnimation();
        this.player.stop();
      }
    },

    reset() {
      this.stop();
      this.endTime = '00:00';
    },

    playerProgress(state) {
      if (state.now >= state.end) {
        this.stop();
      } else {
        this.curTime = formatTime(state.now);
        this.endTime = formatTime(state.end);
        const progress = Math.round(state.now / state.end * 100);
        if (progress !== this.progress) {
          this.progress = progress;
        }
      }
    }
  }
};

function formatTime(time) {
  const min = time / 60 >> 0;
  const sec = time - (min * 60) >> 0;
  return (min < 10 ? '0' + min : min) + ':' + (sec < 10 ? '0' + sec : sec);
}
</script>

<style scoped>
#root {
  display: flex;
  align-items: center;
}

.progress {
  width: 300px;
}

.time.stopped {
  opacity: 0.38;
}
</style>
