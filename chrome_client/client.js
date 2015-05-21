var manifest = null;
var remaining = [];

var savingManifest = false;
var currentURL = null;
var currentEntry = null;
var currentId = null;

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
	savingManifest = true;

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
		currentId = downloadId;
	});
}

function download() {
	if (remaining.length === 0) {
		saveManifest();
		return;
	}

	var e = remaining.pop();

	currentURL = e.url;
	currentEntry = e.entry;

	currentEntry.path = randomName();

	chrome.downloads.download({
		url: e.url,
		saveAs: false,
		filename: "offp/" + currentEntry.path
	}, function(downloadId) {
		log("Downloading #" + downloadId);

		currentId = downloadId;
	});
}

/*function onFileLoaded(event) {
	savingManifest = false;
	manifest = JSON.parse(event.target.result);

	for (var url in manifest) {
        if (!manifest.hasOwnProperty(url)) {
            continue;
        }

        var entry = manifest[url];
        if (!entry.local) {
            remaining.push({ url: url, entry: entry });
        }
    }

	log("Ready to download " + remaining.length + " files");

	download();
}*/

function parseManifest(text) {
	savingManifest = false;
	manifest = JSON.parse(text);

	for (var url in manifest) {
        if (!manifest.hasOwnProperty(url)) {
            continue;
        }

        var entry = manifest[url];
        if (!entry.local) {
            remaining.push({ url: url, entry: entry });
        }
    }

	log("Ready to download " + remaining.length + " files");

	download();
}

function onDownloadChanged(delta) {
	if (delta.id !== currentId) {
		return;
	}

	if (delta.state && delta.state.current === "complete") {
		if (savingManifest) {
			log("Finished.");
			chrome.downloads.erase({ id: currentId });
			return;
		}

		currentEntry.local = true;

		chrome.downloads.search({ id: currentId }, function(items) {
			var item = items[0];

			console.log("finished:", item);

			var f = item.filename;
			currentEntry.path = f.substring(f.lastIndexOf('/') + 1, f.length);
			currentEntry.status = 200;
			currentEntry.headers = {
				'content-type': item.mime
			};
		});

		chrome.downloads.erase({ id: currentId });
		download();
	}
}

window.addEventListener('load', function() {
	chrome.downloads.onChanged.addListener(onDownloadChanged);

	/*var fileInput = document.getElementById("button");
	fileInput.addEventListener('change', function(event) {
		var f = new FileReader();
		f.onload = onFileLoaded;

		f.readAsText(event.target.files[0]);
	});*/

	var inputField = document.getElementById("manifestInput");
	var button = document.getElementById("button");
	button.addEventListener('click', function() {
		parseManifest(inputField.value);
	});
}, false);
