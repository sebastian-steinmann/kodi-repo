const fs = require('fs');
const path = require('path');
const xml2js = require('xml2js');
const parser = new xml2js.Parser();
const JSZip = require("jszip");
const md5File = require('md5-file')
const rimraf = require('rimraf');

const config = {
	src: './src',
	dest: './plugins'
}

const plugins = fs.readdirSync(config.src);
const addonsList = [];
if (!fs.lstatSync(config.dest)) {
	fs.mkdirSync(config.dest);
}
iterateAddons(plugins, 0, createAddonsXml);

function iterateAddons(plugins, index, cb) {
	if (index < plugins.length) {
		return zipAddon(plugins[index], () => iterateAddons(plugins, index + 1, cb))
	}
	return cb();
}

function zipAddon(plugin, cb) {
	const srcFolder = path.join(config.src, plugin);
	const destDir = path.join(config.dest, plugin);

	const addonsrc = fs.readFileSync(path.join(srcFolder, 'addon.xml'),{encoding: 'utf-8'});
	addonsList.push(addonsrc);
	parser.parseString(addonsrc, (err, data) => {
		const version = data.addon.$.version;
		
		const zip = new JSZip();
		const zipFolder = zip.folder(plugin);
		addFilesRec(zipFolder, srcFolder);
		
		if (!fs.lstatSync(destDir)) {
			fs.mkdirSync(destDir);
		}
		// Copy icon file
		fs.writeFileSync(path.join(destDir, 'icon.png'), fs.readFileSync(path.join(srcFolder, 'icon.png')));
		
		const zipFile = path.join(config.dest, plugin, `${plugin}-${version}.zip`);
		zip.generateNodeStream({type:'nodebuffer', streamFiles: false})
			.pipe(fs.createWriteStream(zipFile))
			.on('finish', function () {
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
	const hash = md5File.sync(path.resolve(filename));
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