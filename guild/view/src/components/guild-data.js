/* Copyright 2017-2019 TensorHub, Inc.
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

export function fetchData(path, cb) {
  return _fetch(_dataUrl(path), cb);
}

function _dataUrl(base) {
  return base + window.location.search;
}

function _fetch(path, cb) {
  var url = process.env.VIEW_BASE + path;
  fetch(url).then(function(resp) {
    return resp.json();
  }).then(function(json) {
    cb(json);
  });
}
