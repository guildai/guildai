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

export function formatRuns(runs) {
  return runs.map(formatRun);
}

function formatRun(run) {
  var formattedAttrs = {
    icon: statusIcon(run.status)
  };
  return Object.assign(formattedAttrs, run);
}

function statusIcon(status) {
  if (status === 'completed') {
    return {
      color: 'green',
      icon: 'check-circle',
      tooltip: 'Completed'
    };
  } else if (status === 'error') {
    return {
      color: 'red',
      icon: 'alert',
      tooltip: 'Failed'
    };
  } else if (status === 'terminated') {
    return {
      color: 'teal lighten-2',
      icon: 'close-circle',
      tooltip: 'Terminated'
    };
  } else if (status === 'running') {
    return {
      color: 'orange',
      icon: 'dots-horizontal-circle',
      tooltip: 'Running'
    };
  } else {
    return {
      color: 'grey',
      icon: 'help-circle',
      tooltip: status
    };
  }
}

export function formatScalar(n) {
  if (Number.isInteger(n)) {
    return n;
  } else if (n) {
    return n.toPrecision(4);
  } else {
    return n;
  }
}
