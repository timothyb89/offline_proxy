var manifest = null;
var remaining = [];

var manifestId = null;

function log(text) {
	var dest = document.getElementById("log");

	var node = document.createElement("li");
	node.innerHTML = text;

	dest.appendChild(node);
}

function randomName() {
	return "cache-"
			+ (Math.random() + 1).toString(36).substring(2)
			+ ".bin";
}

function saveManifest() {
	console.log("saving:", manifest);
	log("Downloads finished, saving manifest...");

	var json = JSON.stringify(manifest);
	var enc = window.btoa(json);

	chrome.downloads.download({
		url: 'data:text/plain;base64,' + enc,
		saveAs: false,
		filename: 'offp/metadata.json',
		conflictAction: 'overwrite'
	}, function(downloadId) {
		manifestId = downloadId;
	});
}

function download() {
	if (remaining.length === 0) {
		saveManifest();
		return;
	}

	chrome.downloads.download({
		url: remaining.pop(),
		saveAs: false,
		filename: "offp/" + randomName()
	}, function(downloadId) {
		log("Downloading #" + downloadId);
	});
}

function parseManifest(text) {
	manifest = JSON.parse(text);

	for (var url in manifest) {
        if (!manifest.hasOwnProperty(url)) {
            continue;
        }

        var entry = manifest[url];
        if (!entry.local) {
            remaining.push(url);
        }
    }

	log("Ready to download " + remaining.length + " files");

	download();
}

function onDownloadChanged(delta) {
	chrome.downloads.search({ id: delta.id }, function(items) {
		if (items.length === 0) {
			return;
		}

		var item = items[0];

		var currentEntry = manifest[item.url];
		if (typeof(currentEntry) === "undefined") {
			return;
		}

		if (delta.error) {
			chrome.downloads.erase({ id: delta.id });
			console.log("skipping due to error", delta);
			download(); // move on
		}

		if (delta.state && delta.state.current === "complete") {
			if (manifestId !== null && delta.id === manifestId) {
				log("Finished.");
				chrome.downloads.erase({ id: delta.id });
				return;
			}

			console.log("finished:", item);

			var f = item.filename;
			currentEntry.path = f.substring(f.lastIndexOf('/') + 1, f.length);
			currentEntry.local = true;
			currentEntry.status = 200;

			currentEntry.headers = {};
			if (item.mime) {
				currentEntry.headers['content-type'] = item.mime;
			} else {
				currentEntry.headers['content-type'] = 'text/plain';
			}

			chrome.downloads.erase({ id: delta.id });
			download();
		}
	});

}

window.addEventListener('load', function() {
	chrome.downloads.onChanged.addListener(onDownloadChanged);

	var inputField = document.getElementById("manifestInput");
	var button = document.getElementById("button");
	button.addEventListener('click', function() {
		parseManifest(inputField.value);
	});
}, false);
