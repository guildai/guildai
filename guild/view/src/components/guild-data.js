export function fetchData(path, route, cb) {
  return _fetch(_dataUrl(path, route), cb);
}

function _dataUrl(base, route) {
  var path = route.fullPath;
  var i = path.indexOf('?');
  return i !== -1 ? base + '?' + path.substring(i + 1) : base;
}

function _fetch(path, cb) {
  var url = process.env.VIEW_BASE + path;
  fetch(url).then(function(resp) {
    return resp.json();
  }).then(function(json) {
    cb(json);
  });
}
