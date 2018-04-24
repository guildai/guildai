<template>
  <v-dialog
    ref="viewer"
    v-model="visible"
    scrollable
    :fullscreen="fullscreen">
    <v-card id="card">
      <v-card-title id="card-title" class="grey lighten-4">
        <v-select
          v-if="files"
          :items="files"
          v-model="selectedPath"
          item-text="path"
          item-value="path"
          single-line
          :prepend-icon="selectedIcon" />
        <v-spacer v-else />
        <ul class="meta">
          <li v-for="val in viewerMeta">{{ val }}</li>
          <li>{{ selectedSize }}</li>
          <li>{{ selectedMtime }}</li>
        </ul>
        <v-btn
          v-if="fullscreen"
          icon flat
          @click="fullscreen = false">
          <v-icon>mdi-fullscreen-exit</v-icon>
        </v-btn>
        <v-btn
          v-else
          icon flat
          @click="fullscreen = true">
          <v-icon>mdi-fullscreen</v-icon>
        </v-btn>
        <v-btn
          icon flat @click="visible = false">
          <v-icon>clear</v-icon>
        </v-btn>
      </v-card-title>
      <v-divider />
      <v-card-text class="content">
        <template v-if="selected">
          <guild-image-viewer
            v-if="selected.viewer === 'image'"
            :src="selectedSrc"
            @meta="viewerMeta = $event" />
          <guild-text-viewer
            v-else-if="selected.viewer === 'text'"
            :src="selectedSrc" />
          <guild-midi-viewer
            v-else-if="selected.viewer === 'midi'"
            :src="selectedSrc"
            :active="visible" />
          <guild-table-viewer
            v-else-if="selected.viewer === 'table'"
            :src="selectedSrc"
            />
          <div v-else>
            Unsupported viewer type: <i>{{ selected.viewer }}</i>
          </div>
        </template>
        <template v-else>
          No files to view
        </template>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="grey lighten-4">
        <v-btn flat :disabled="files.length <= 1" @click="nav(-1)">Prev</v-btn>
        <v-spacer />
        <v-btn flat :disabled="files.length <= 1" @click="nav(1)">Next</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import filesize from 'filesize';

export default {
  name: 'guild-files-viewer',

  props: {
    files: {
      type: Array,
      required: true
    },
    path: String,
    srcBase: {
      type: String,
      default: ''
    },
    value: Boolean
  },

  data() {
    return {
      selectedPath_: undefined,
      fullscreen: false,
      viewerMeta: []
    };
  },

  computed: {
    visible: {
      get() {
        return this.value;
      },
      set(val) {
        this.$emit('input', val);
      }
    },

    selectedPath: {
      get() {
        if (this.selectedPath_) {
          return this.selectedPath_;
        } else {
          return this.path;
        }
      },
      set(val) {
        this.selectedPath_ = val;
      }
    },

    selectedIndex() {
      for (var i = 0; i < this.files.length; i++) {
        if (this.files[i].path === this.selectedPath) {
          return i;
        }
      }
      return -1;
    },

    selected() {
      return this.selectedIndex !== -1
           ? this.files[this.selectedIndex]
           : undefined;
    },

    selectedIcon() {
      if (this.selected && this.selected.icon) {
        return 'mdi-' + this.selected.icon;
      } else {
        return undefined;
      }
    },

    selectedSrc() {
      if (this.selected) {
        return this.srcBase + this.selected.path;
      } else {
        return undefined;
      }
    },

    selectedSize() {
      if (this.selected && this.selected.size !== null) {
        return filesize(this.selected.size);
      } else {
        return '';
      }
    },

    selectedMtime() {
      if (this.selected && this.selected.mtime !== null) {
        const date = new Date(this.selected.mtime);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
      } else {
        return '';
      }
    }
  },

  watch: {
    visible(val) {
      if (!val) {
        this.selectedPath_ = undefined;
      }
    }
  },

  created() {
    window.addEventListener('keydown', this.onKeyDown);
  },

  destroyed() {
    window.removeEventListener('keydown', this.onKeyDown);
  },

  methods: {
    onKeyDown(e) {
      if (!this.value || e.defaultPrevented) {
        return;
      }
      if (e.keyCode === 27) { // Esc
        this.visible = false;
      } else if (e.keyCode === 37) { // Left
        this.nav(-1);
      } else if (e.keyCode === 39) { // Right
        this.nav(1);
      }
    },

    nav(incr) {
      var nextIndex = maybeWrapIndex(this.selectedIndex + incr, this.files);
      this.viewerMeta = [];
      this.selectedPath = this.files[nextIndex].path;
    }
  }
};

function maybeWrapIndex(index, array) {
  if (index < 0) {
    return array.length - 1;
  } else if (index >= array.length) {
    return 0;
  } else {
    return index;
  }
};
</script>

<style>
.input-group__prepend-icon {
  min-width: 32px !important;
}

.input-group__details {
  max-width: calc(100% - 32px) !important;
  min-height: 16px !important;
}
</style>

<style scoped>
#card {
  max-height: 100%;
  min-height: 480px;
}

#card-title {
  padding: 8px 4px 8px 16px;
}

.input-group {
  padding-right: 16px;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #666;
  height: 100%;
}

.meta {
  margin: 0 15px 0 10px;
}

.meta li {
  display: inline;
  margin: 0 8px;
}
</style>
