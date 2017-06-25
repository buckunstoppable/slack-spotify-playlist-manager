import atexit, json, os, signal, sys, urllib
import functions as f

def getCreds(r, creds=None):
	with open(os.path.join(r,"env","slack.json")) as creds:
		allCreds = json.load(creds)
	return allCreds

def goodbye():
	print("Goodbye!")
	return sys.exit()

def handler(signum, frame):
    goodbye()

ROOT = os.path.abspath(os.path.dirname(__file__))
creds = getCreds(ROOT)
slackConnection = f.slack.start(creds["slack"]["token"])
slackChannels = f.slack.getSlackChannels(creds["channel-playlist-pairs"])

try: 
	if not slackConnection.rtm_connect():
		print("Could not connect to Slack.")
		goodbye()

	# Define interruption handling
	# atexit.register(f.slack.setChannelTopic, client = slackConnection, channel = slack["channel"], running = None)
	signal.signal(signal.SIGTERM, handler)
	signal.signal(signal.SIGINT, handler)

	# Begin listening loop
	while True:
		print("\nBeginning new loop to listen for contact from Slack...")
		messageChannel = None
		# Loop until a user has shared a Spotify link in an approved channel
		while not (messageChannel and urls):
			botWasBullied = False
			for slackMessage in slackConnection.rtm_read():
				messageChannel, urls, botWasBullied = f.slack.awaitContact(slackMessage, slackChannels, creds["spotify"]["urlbase"], creds["slack"]["botId"])
				if botWasBullied: 
					f.slack.sendAntiBullyingMessage(slackConnection, messageChannel, creds["slack"]["botId"])
					continue
		trackIds = f.spotify.extractTrackIds(creds["spotify"]["urlbase"], urls)
		print ("trackIds are", trackIds)
		if trackIds:
			spotifyInstance = f.spotify.getSpotifyInstance(creds["spotify"]["username"], creds["spotify"]["id"], creds["spotify"]["secret"], creds["spotify"]["redirect"])
			
			if spotifyInstance:
				playlistId = f.spotify.getPlaylist(messageChannel, creds["channel-playlist-pairs"])
				playlistName, playlistUrl = f.spotify.getPlaylistInfo(spotifyInstance, creds["spotify"]["username"], playlistId)
				
				for trackId in trackIds:
					trackName = f.spotify.getTrackName(spotifyInstance, trackId)
					print trackId
					trackList = f.spotify.getPlaylistTracks(spotifyInstance, creds["spotify"]["username"], playlistId, f.spotify.getPlaylistTotalTracks(spotifyInstance, creds["spotify"]["username"], playlistId))
					if trackId not in trackList:
						f.spotify.postToPlaylist(spotifyInstance, creds["spotify"]["username"], playlistId, urls)
						f.slack.sendSuccessNotification(slackConnection, messageChannel, trackName, playlistName, playlistUrl)
					else:
						f.slack.sendSkipNotification(slackConnection, messageChannel, trackName, playlistName, playlistUrl)
						continue

except (KeyboardInterrupt):
	goodbye()