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

def getChannelMembers(client, channel):
	response = client.api_call("channels.info", channel=channel)
	return response["channel"]["members"]

def getBotId(client, botId):
	response = client.api_call("users.info", user=botId)
	return response["user"]["profile"]["bot_id"]

def attachment():
	return [
        {
            "fallback": "",
            "color": "#a63636",
            "title": "Song of the Day",
        }
    ]

def bullyingStatements():
	return ["fuck you", "fucker", "shut up", "die", "go to hell", "piss off", "i hate you", "you suck", "sucks", "loser", "u suck", "fuck u", "eat shit", ":middle_finger:", ":reversed_hand_with_middle_finger_extended:", "your momma", "your mom", "ur momma", "ur mom"]

def awaitContact(slackMessage, validChannels, validUrlBase, botId, urls=None):
	messageChannel = slackMessage.get("channel")

	# Parse only messages that are in the proper channel, and not sent by the bot itself
	if messageChannel in validChannels:
		messageType = slackMessage.get("type")
		body = slackMessage.get("text")
		user = slackMessage.get("bot_id")
		if messageType == 'message' and body and botId in body and any(x in body.lower() for x in bullyingStatements()):
			return messageChannel, None, True
		if user != botId and messageType == 'message' and body and validUrlBase in body:
			urls = extractUrls(body)
			for url in urls:
				if validUrlBase not in url:
					urls.remove(url)
			return messageChannel, urls, False
	return None, None, None

def sendMessage(client, channel, text):
	client.api_call("chat.postMessage", username="music-bot", channel=channel, text=text, unfurl_links=False, unfurl_media=False)

# Send song suggestion that requires an emoji reaction
def sendMessageForReaction(client, channel, text):
	response = client.api_call("chat.postMessage", username="music-bot", channel=channel, attachments=attachment(), text=text)
	print(response)
	return response["ts"], None

# Determine what user has reacted with
def parseReaction(origThread, slackMessage, validUsers, userReaction=None, user=None):
	positives = ["+1", "thumbsup", "fire", "boom"]
	negatives = ["-1", "thumbsdown"]
	messageType = slackMessage.get("type")
	if messageType == "reaction_added":
		user = slackMessage.get("user")
		reaction = slackMessage.get("reaction")
		print "reaction added is %s" % reaction
		item = slackMessage.get("item")
		print "Thread passed in: %s" % origThread
		print "valid"
		print(item)
		if item and item["ts"] == origThread and user in validUsers:
			userReaction = True if reaction in positives else False if reaction in negatives else None
	print (userReaction)
	return userReaction, user if userReaction is not None else None

# Wait for a set amount of time, for a required number of users to approve or disapprove of the song
def reactionLoop(client, channel, users, text, approvalsRequired, rejectionsRequired, expiration):
	reactThread, approved = sendMessageForReaction(client, channel, text)
	print "reactThread is: %s" % reactThread
	for x in range(0, approvalsRequired):
		while approved is None:
			for message in client.rtm_read():
				approved, user = parseReaction(reactThread, message, users)
		print "approved is %s" % approved
		if not approved: rejectionsRequired = rejectionsRequired - 1
		if rejectionsRequired == 0: return False
		users.remove(user)
		approved = None
	return True