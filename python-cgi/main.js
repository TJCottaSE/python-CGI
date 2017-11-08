// Web Server
var cgi = require('cgi');
var http = require('http');
const path = require('path');
console.log("Current Directory is " + __dirname);
var script = path.resolve(__dirname, /*'test-cgi.sh'*/'cgi-bin', 'run10.py');
console.log("Script path is: " + script);
http.createServer(/*callback*/cgi(script) ).listen(8080);


//http.createServer(function (req, res) {
//	res.writeHead(200, {'Content-Type': 'text/plain'});
//	res.end('Hello World\n');
//   }).listen(8081);
console.log('Server started');