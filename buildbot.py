#!/usr/bin/env python3
import configparser, datetime, os, sys, urllib.request, json, platform, subprocess

###

BIN_DIR = os.path.dirname(os.path.realpath(__file__))

CONFIG = configparser.ConfigParser()
CONFIG.read_dict({
	'buildbot:slack' : {
		"url" : '',
		"channel" : '',
	}
})
CONFIG.read(os.path.join(BIN_DIR,'buildbot.conf'))

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
		"channel": CONFIG.get("availmon:slack", "channel", fallback="#apitest"),
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
	p = subprocess.Popen(["/home/ateska/Workspace/seacat/buildbot/build.sh"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd="/home/ateska/Workspace/seacat/server")
	out, err = p.communicate()

	slack_text = []
	slack_attachments = {}

	if p.returncode == 0:
		status = "OK"
		#slack_text.append("Build OK")
	else:
		status = "FAILED"
		slack_text.append("Return code: {}".format(p.returncode))

	if out is not None:
		out = out.decode('utf-8')
		out_arr = []

		for line in out.split('\n'):
			if contains_warns(line):
				out_arr.append(line)

			if line.startswith("GIT_VERSION: "):
				slack_text.append("Version: {}".format(line[13:].strip()))

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

	if not os.path.exists("/home/ateska/Workspace/seacat/buildbot/logs/"):
		os.makedirs("/home/ateska/Workspace/seacat/buildbot/logs/")
	open("/home/ateska/Workspace/seacat/buildbot/logs/out.txt", "w").write(out)

if __name__ == '__main__':
	os.chdir(BIN_DIR)
	sys.exit(main())
