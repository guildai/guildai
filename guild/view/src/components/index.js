/* Copyright 2017-2022 TensorHub, Inc.
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

import GuildCompare from './guild-compare.vue';
import GuildFilesViewer from './guild-files-viewer.vue';
import GuildImageViewer from './guild-image-viewer.vue';
import GuildMidiViewer from './guild-midi-viewer.vue';
import GuildRun from './guild-run.vue';
import GuildRunFiles from './guild-run-files.vue';
import GuildRunOutput from './guild-run-output.vue';
import GuildRunOverview from './guild-run-overview.vue';
import GuildRunStatusIcon from './guild-run-status-icon.vue';
import GuildRunTitlebar from './guild-run-titlebar.vue';
import GuildTableViewer from './guild-table-viewer.vue';
import GuildTextLoader from './guild-text-loader.vue';
import GuildTextViewer from './guild-text-viewer.vue';
import GuildView from './guild-view.vue';
import GuildViewFooter from './guild-view-footer.vue';
import GuildViewSelect from './guild-view-select.vue';
import GuildViewToolbar from './guild-view-toolbar.vue';
import GuildViewWaiting from './guild-view-waiting.vue';

GuildView.install = function install(Vue) {
  const component = function(c) {
    Vue.component(c.name, c);
  };
  component(GuildCompare);
  component(GuildFilesViewer);
  component(GuildImageViewer);
  component(GuildMidiViewer);
  component(GuildRun);
  component(GuildRunFiles);
  component(GuildRunOutput);
  component(GuildRunOverview);
  component(GuildRunStatusIcon);
  component(GuildRunTitlebar);
  component(GuildTableViewer);
  component(GuildTextLoader);
  component(GuildTextViewer);
  component(GuildView);
  component(GuildViewFooter);
  component(GuildViewSelect);
  component(GuildViewToolbar);
  component(GuildViewWaiting);
};

export default GuildView;
