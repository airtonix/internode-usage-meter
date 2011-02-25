#!/usr/bin/env python
import urllib, urllib2
import os, sys, re
from optparse import OptionParser
import logging
import logging.config

class Poller:
	server_url = "https://customer-webtools-api.internode.on.net/cgi-bin/padsl-usage"
	pattern = r"(?P<used>[\d]+\.[\d]+)\ (?P<quota>[\d]+)\ (?P<rollover_date>[\d]{1,2}\/[\d]{1,2}\/[\d]{2,4})\ (?P<extra_cost>[\d]+\.[\d]+)"
	csv_header = "Timestamp, Request Time, Used, Quota, Rollover Date, Extra Costs\n"
	logging_format = "%(created)f, %(relativeCreated)d, %(message)s"
	row_format="%(used)s, %(used)s, %(rollover_date)s, %(extra_cost)s"

	def __init__(self, options):
		self.options = options
		self.header_data = urllib.urlencode([
			('username', self.options.username),
			('password', self.options.password)
		])
		self.request = urllib2.Request(self.server_url)
		self.regex_pattern = re.compile(self.pattern)

		self.config_path = "%s/.config/internode-usage-meter" % os.getenv("HOME")
		self.log_path = "%s/.local/logs/internode-usage-meter" % os.getenv("HOME")

		if not os.path.exists(self.config_path):
			os.makedirs(self.config_path)
		if not os.path.exists(self.log_path):
			os.makedirs(self.log_path)
		self.config_file_path = os.path.join(self.config_path, "logging.conf")

		if not options.filename :
			self.logfilepath = os.path.join(self.log_path, "%s.log" % options.username)
		else:
			self.logfilepath = options.filename


		self.start_logging()

	def start_logging(self):
#		if not os.path.exists(self.config_file_path):
#			logging.config.fileConfig(self.config_file_path)
#			logger = logging.getLogger("internode_usage_meter")

#		else :
		if not os.path.exists(self.logfilepath) :
			logfile = open(self.logfilepath,"w")
			logfile.write(self.csv_header)
			logfile.close()

		logger = logging.getLogger("internode_usage_meter")
		logger.setLevel(logging.INFO)
		formatter = logging.Formatter(self.logging_format)
		file_logger = logging.FileHandler(filename=self.logfilepath)
		file_logger.setFormatter(formatter)
		logger.addHandler(file_logger)

		self.logger = logger

	def query(self):
		response = urllib2.urlopen(self.request, self.header_data)
		self.data = response.read()
		return self.data

	def report(self, graph=False):
		match = self.regex_pattern.search(self.data)
		if match :
			data = match.groups()
			self.logger.info(self.row_format % match.groupdict())
		else :
			self.logger.error(self.data)

	def generate_graph(self):
		if self.options.graph_file and os.path.exists(self.logfilepath):
			log_file = open(self.logfilepath,"r")
			log_file_data = []
			log_file_lines = log_file.read().split("\n")
			log_file_lines.pop(0)
			for line in log_file_lines:
				log_file_data.append( line.split(",") )
			print log_file_data


if __name__ == "__main__" :
	parser = OptionParser()
	parser.add_option("-U", "--username",
		dest="username",
		help="logon username")
	parser.add_option("-P", "--password",
		dest="password",
		help="logon password")

	parser.add_option("-L", "--log-file",
		dest="filename",
		help="append report to FILE",
		metavar="FILE")
	parser.add_option("-G", "--graph-image-file",
		dest="graph_file",
		help="filename to save graphed image data.")

	parser.add_option("-q", "--quiet",
		action="store_false",
		dest="verbose",
		default=True,
		help="don't print status messages to stdout")

	(options, args) = parser.parse_args()
	if options.username and options.password :
		poller = Poller(options)
		poller.query( )
		poller.report()
		if options.graph_file :
			poller.generate_graph()
	else :
		parser.print_help()

