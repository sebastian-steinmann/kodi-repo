const fs = require('fs');
const path = require('path');
const xml2js = require('xml2js');
const parser = new xml2js.Parser();
const JSZip = require("jszip");
const checksum = require('checksum');
const rimraf = require('rimraf');

const config = {
	src: './src',
	dest: './plugins'
}

/***
clean dest
read addonsxml
create zip of src
copy to version number folder dest
create md5 of zip
create addons.xml
create md5 og xml
***/

const plugins = fs.readdirSync(config.src);
const addonsList = [];
rimraf(config.dest, () => {
	fs.mkdir(config.dest, () => {
		iterateAddons(plugins, 0, createAddonsXml);
	});
});



function iterateAddons(plugins, index, cb) {
	if (index < plugins.length) {
		return zipAddon(plugins[index], () => iterateAddons(plugins, index + 1, cb))
	}
	return cb();
}

function zipAddon(plugin, cb) {
	console.log(plugin);
	const addonsrc = fs.readFileSync(path.join(config.src, plugin, 'addon.xml'),{encoding: 'utf-8'});
	addonsList.push(addonsrc);
	parser.parseString(addonsrc, (err, data) => {
		console.log('got xml');
		const version = data.addon.$.version;
		const zip = new JSZip();
		var dir = path.join(config.src, plugin);
		addFilesRec(zip, dir);

		fs.mkdirSync(path.join(config.dest, plugin));

		const zipFile = path.join(config.dest, plugin, `${plugin}-${version}.zip`);
		zip.generateNodeStream({type:'nodebuffer', streamFiles: true})
			.pipe(fs.createWriteStream(zipFile))
			.on('finish', function () {
				console.log('zip created')
				createChecksumFile(zipFile);
				cb();
			});
	});
}

function createAddonsXml() {
	const addons = addonsList.map(addonXml => {
		return addonXml.split('>').slice(1).join('>');
	}).join('\n');
	const pre = '<?xml version="1.0" encoding="UTF-8"?>\
					<addons>';
	const post = '</addons>';
	const xml = `${pre}
				${addons}
				${post}`;
	const filename = path.join(config.dest, 'addons.xml');
	fs.writeFileSync(filename, xml);
	createChecksumFile(filename);
}

function createChecksumFile(filename) {
	const hash = checksum(path.resolve(filename), { algorithm: 'md5' });
    fs.writeFileSync(filename + '.md5', hash); //CB sends it away
}

function addFilesRec(zip, dir) {
	fs.readdirSync(dir).forEach(file => {
		const absPath = path.resolve(dir, file);
		const stat = fs.lstatSync(absPath);
		if (stat && stat.isDirectory()) {
			addFilesRec(zip.folder(file), absPath);
		} else {
			zip.file(file, fs.readFileSync(absPath));
		}
	});
}