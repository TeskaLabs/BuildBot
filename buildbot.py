#!/usr/bin/env python3
import argparse
import logging
import configparser, datetime, os, sys, urllib.request, json, platform, subprocess

###

L = logging.getLogger(__name__)

###

BIN_DIR = os.path.dirname(os.path.realpath(__file__))

CONFIG = configparser.ConfigParser()
CONFIG.read_dict({
	'general': {
		'config_file': os.path.join(BIN_DIR,'buildbot.conf'),
		'log_dir': '/home/ateska/Workspace/seacat/buildbot/logs/',
	},
	'buildbot' : {
		'exec': '/home/ateska/Workspace/seacat/buildbot/build.sh',
		'working_directory': '/home/ateska/Workspace/seacat/server',
	},
	'buildbot:slack' : {
		"url" : '',
		"channel" : '',
	}
})

parser = argparse.ArgumentParser(
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="Buildbot\n2018 TeskaLabs Ltd\nhttps://www.teskalabs.com/\n\n",
)
parser.add_argument('-c', '--config', help='Specify file path to configuration file')
args = parser.parse_args()
if args.config is not None:
	CONFIG['general']['config_file'] = args.config

CONFIG.read(CONFIG['general']['config_file'])

###

def send_slack_message(status, text, attachments):
	url = CONFIG.get("buildbot:slack", "url")
	if url is None or url == '':
		L.info("No Slack URL is given")
		return;


	dt = datetime.datetime.utcnow()

	status_color_map = {
		"OK": "good",
		"WARN": "warning",
		"FAILED": "danger"
	}
	status_color = status_color_map.get(status, "danger")

	data = {
		"channel": CONFIG.get("buildbot:slack", "channel", fallback="#apitest"),
		"username": "BuildBot",
		"icon_emoji": ":robot_face:",
		
		"attachments":[
			{
				"color": status_color,
				"fallback": "{} @ {}".format(status, platform.node().partition('.')[0]),
				"title": "{} @ {}".format(status, platform.node().partition('.')[0]),
				"text": text,
				"mrkdwn_in": ["fields"],
				"fields": [
				],
				"footer": "BuildBot",
				"ts": int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
			}
		],
	}

	f = data["attachments"][0]["fields"]
#	a = alerts.pop('*')
#	if a is not None:
#		f.append({"value": '\n'.join(a), "short": False})
#
	for k, v in attachments.items():
		f.append({"title": k, "value": '\n'.join(v), "short": False})

	req = urllib.request.Request(url=url, data=json.dumps(data).encode('utf-8'), method='POST')
	with urllib.request.urlopen(req) as f:
		pass
	
	if f.status != 200:
		L.error("Failed to submit message to Slack: {} {}".format(f.status, f.reason))

###

def contains_warns(line):
	line = line.lower()
	if 'error' in line: return True
	if 'warn' in line: return True
	if 'fatal' in line: return True
	return False

###

def main():
	p = None
	try:
		p = subprocess.Popen([CONFIG.get("buildbot", "exec")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=CONFIG['buildbot']['working_directory'])
		out, err = p.communicate()
	except Exception as e:
		out = None
		err = str(e).encode('utf-8')

	slack_text = []
	slack_attachments = {}

	if p is not None:
		if p.returncode == 0:
			status = "OK"
			#slack_text.append("Build OK")
		else:
			status = "FAILED"
			slack_text.append("Return code: {}".format(p.returncode))
	else:
		status = "FAILED"

	if out is not None:
		out = out.decode('utf-8')
		out_arr = []

		for line in out.split('\n'):
			if contains_warns(line):
				out_arr.append(line)

			if line.startswith("GIT_VERSION: "):
				slack_text.append("SeaCat Server {}".format(line[13:].strip()))

		if len(out_arr) > 0:
			slack_attachments["STDOUT"] = out_arr
			if status != "FAILED":
				status = "WARN"

	if err is not None:
		err = err.decode('utf-8')
		err_arr = err.split('\n')
		slack_attachments["STDERR"] = err_arr
		if status != "FAILED":
			status = "WARN"

	send_slack_message(status, '\n'.join(slack_text), slack_attachments)

	try:
		if not os.path.exists(CONFIG['general']['log_dir']):
			os.makedirs(CONFIG['general']['log_dir'])
		open(os.path.join(CONFIG['general']['log_dir'], "out.txt"), "w").write(out)
	except Exception as e:
		L.error(e)

if __name__ == '__main__':
	os.chdir(BIN_DIR)
	sys.exit(main())
