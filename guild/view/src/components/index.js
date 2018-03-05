/* Copyright 2017-2018 TensorHub, Inc.
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

import GuildFilesViewer from './guild-files-viewer.vue';
import GuildMidi from './guild-midi.vue';
import GuildRunFiles from './guild-run-files.vue';
import GuildRunOverview from './guild-run-overview.vue';
import GuildRunStatusIcon from './guild-run-status-icon.vue';
import GuildRunTitlebar from './guild-run-titlebar.vue';
import GuildRunsList from './guild-runs-list.vue';
import GuildText from './guild-text.vue';
import GuildView from './guild-view.vue';
import GuildViewToolbar from './guild-view-toolbar.vue';

GuildView.install = function install(Vue) {
  const component = function(c) {
    Vue.component(c.name, c);
  };
  component(GuildFilesViewer);
  component(GuildMidi);
  component(GuildRunFiles);
  component(GuildRunOverview);
  component(GuildRunStatusIcon);
  component(GuildRunTitlebar);
  component(GuildRunsList);
  component(GuildText);
  component(GuildView);
  component(GuildViewToolbar);
};

export default GuildView;
