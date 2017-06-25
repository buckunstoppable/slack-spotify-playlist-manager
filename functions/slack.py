from slackclient import SlackClient
import re

def extractUrls(text):
	urls = re.findall('http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))[^<>]+', text)
	return urls


def start(cred):
	return SlackClient(cred)

def getSlackChannels(pairs, channels=[]):
	for pair in pairs:
		channels.append(pair["channel"])
	return channels

def bullyingStatements():
	return ["fuck you", "fucker", "shut up", "die", "go to hell", "piss off", "i hate you", "you suck", "sucks", "loser", "u suck", "fuck u", "eat shit", ":middle_finger:", ":reversed_hand_with_middle_finger_extended:", "your momma", "your mom", "ur momma", "ur mom"]

def awaitContact(slackMessage, validChannels, validUrlBase, botId, urls=None):
	# Set of accepted input strings to trigger a slackbot response

	messageChannel = slackMessage.get("channel")
	if messageChannel in validChannels:
		messageType = slackMessage.get("type")
		body = slackMessage.get("text")
		if messageType == 'message' and body and botId in body and any(x in body.lower() for x in bullyingStatements()):
			return messageChannel, None, True
		if messageType == 'message' and body and validUrlBase in body:
			urls = extractUrls(body)
			for url in urls:
				if validUrlBase not in url:
					urls.remove(url)
			return messageChannel, urls, False
	return None, None, None

def sendSuccessNotification(client, channel, trackName, playlistName, playlistUrl):
	text = "I've added _%s_ to the Spotify playlist, <%s|%s>. :boom:" % (trackName, playlistUrl, playlistName)
	client.api_call("chat.postMessage", username="qa-bot", icon_emoji=":money_with_wings:", channel=channel, text=text, unfurl_links=False, unfurl_media=False)

def sendSkipNotification(client, channel, trackName, playlistName, playlistUrl):
	text = "_%s_ is a cool song, but it's already in your playlist, <%s|%s>. What were you _thinking_?" % (trackName, playlistUrl, playlistName)
	client.api_call("chat.postMessage", username="qa-bot", icon_emoji=":money_with_wings:", channel=channel, text=text, unfurl_links=False, unfurl_media=False)

def sendAntiBullyingMessage(client, channel, botId):
	text = "Bots have feelings, too, y'know. Bullying makes <@%s> :cry:." % botId
	client.api_call("chat.postMessage", username="qa-bot", icon_emoji=":money_with_wings:", channel=channel, text=text, unfurl_links=False, unfurl_media=False)