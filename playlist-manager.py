import atexit, json, os, random, signal, sys, urllib
from datetime import datetime
from multiprocessing import Process
from threading import Timer
import functions as f

def getCreds(r, creds=None):
	with open(os.path.join(r,"env","test.json")) as creds:
		allCreds = json.load(creds)
	return allCreds

def goodbye():
	print("Goodbye!")
	return sys.exit()

def handler(signum, frame):
    goodbye()

def rejectPath(r, playlistId):
	print os.path.join(r, "rejects", "%s.txt" % playlistId)
	return os.path.join(r, "rejects", "%s.txt" % playlistId)

def initializeRejectFiles(r, pairs):
	for pair in pairs:
		path = rejectPath(r, pair["playlist"])
		file = open(path, "a" if os.path.exists(path) else "w")
		file.close()

def writeToRejects(rejectPath, songOfDayId):
	with open(rejectPath, "a") as rejectFile:
		rejectFile.write("%s\n" % songOfDayId)
	
def scheduledTime():
	current = datetime.today()
#	scheduled = current.replace(day=current.day+1, hour=10, minute=0, second=0, microsecond=0)
	scheduled = current.replace(day=current.day, hour=current.hour if current.minute < 59 else current.hour + 1, minute=current.minute if current.second < 50 else current.minute+1, second=current.second + 10 if current.second < 50 else current.second-50, microsecond=0)
	delay = scheduled - current
	print "scheduled time %s" % scheduled
	return delay.seconds + 1

# Set expiration time for 12 hours after suggestion is made
def expirationTime():
	current = datetime.today()
	return current.replace(day=current.day if current.hour < 12 else current.day + 1, hour=current.hour+12 if current.hour < 12 else current.hour-12, minute = current.minute, second=current.second, microsecond = current.microsecond)

def expirationTimeDisplay(expiration):
	return expiration.strftime("%m/%d/%Y %I:%M %p")

# def songAdded(spotifyInstance, username, playlistId, urls):
#	f.spotify.postToPlaylist(spotifyInstance, username, playlistId, urls)
#	f.slack.sendMessage(slackConnection, messageChannel, f.messages.songAdded(trackName, playlistUrl, playlistName))

def getSeedSongs(trackList, songsNeeded):
	seedSongs = []
	for x in range(0,songsNeeded):
		selected = random.choice(trackList)
		seedSongs.append(selected)
		trackList.remove(selected)
	return seedSongs

def handleSuggestion(r, client, spotifyInstance, username, pair):
	approvalsRequired, rejectionsRequired, runs, rejectList, recommendList = 1, 1, 0, [], []
	rejectFilePath = rejectPath(r, pair["playlist"])
	with open(rejectFilePath, "r") as rejects:
		rejectList = [reject.strip() for reject in rejects]
	trackList = f.spotify.getPlaylistTracks(spotifyInstance, username, pair["playlist"], f.spotify.getPlaylistTotalTracks(spotifyInstance, username, pair["playlist"]))

	while runs < 5 and len(recommendList) < 10:
		seedList = getSeedSongs(trackList[:], 5 - len(pair["genres"]))
		recommendations = f.spotify.getRecommendations(spotifyInstance, pair["genres"], seedList)
		if recommendations:
			for r in recommendations["tracks"]:
				if (trackList and r["id"] in trackList) or (rejectList and r["id"] in rejectList): continue
				recommendList.append(r["id"])

	if not recommendList:
		f.slack.sendMessage(client, pair["channel"], f.messages.couldNotGetSong())
	else:
		songOfDayId = random.choice(recommendList)

		userChoice = f.slack.reactionLoop(client, pair["channel"], f.slack.getChannelMembers(client, pair["channel"]), f.messages.songRecommendation(f.spotify.buildTrackUrl(songOfDayId), approvalsRequired, rejectionsRequired, expirationTimeDisplay(expirationTime())), approvalsRequired, rejectionsRequired, expirationTime())
		if userChoice is not None:
			if userChoice: f.spotify.postToPlaylist(spotifyInstance, username, pair["playlist"], songOfDayId)
			else: writeToRejects(rejectFilePath, songOfDayId)

def runInParallel(r, client, spotifyInstance, username, pairs):
	proc = []
	for pair in pairs:
		if pair["channel"] != "C3PRNS8DR": pass
		# For recommendations to be at all accurate, config must specify at least one musical genre to define the nature of the playlist.
		# Recommendations will *NOT* be generated for playlists organized around something other than a limited set of genres.
		if len(pair["genres"]) > 0:
			p = Process(target=handleSuggestion(r, client, spotifyInstance, username, pair))
			p.start()
			proc.append(p)
	for p in proc:
		p.join()

def runSuggestionJob(r, creds, client):
	# Create track suggestion for each channel (on weekdays only)
	spotifyInstance = f.spotify.getSpotifyInstance(creds["spotify"]["username"], creds["spotify"]["id"], creds["spotify"]["secret"], creds["spotify"]["redirect"])

#	if spotifyInstance and datetime.today().weekday() < 5:
	if spotifyInstance:
		runInParallel(r, client, spotifyInstance, creds["spotify"]["username"], creds["channel-playlist-pairs"])

	# Schedule another
	Timer(scheduledTime(), runSuggestionJob, [r, creds, client]).start()

ROOT = os.path.abspath(os.path.dirname(__file__))
creds = getCreds(ROOT)
initializeRejectFiles(ROOT, creds["channel-playlist-pairs"])
slackConnection = f.slack.start(creds["slack"]["token"])
slackSuggestionConnection = f.slack.start(creds["slack"]["token"])
slackChannels = f.slack.getSlackChannels(creds["channel-playlist-pairs"])
slackRawBotId = f.slack.getBotId(slackConnection, creds["slack"]["botId"])

try: 
	if not (slackConnection.rtm_connect() and slackSuggestionConnection.rtm_connect()):
		print("Could not connect to Slack.")
		goodbye()

	# Define interruption handling
	# atexit.register(f.slack.setChannelTopic, client = slackConnection, channel = slack["channel"], running = None)
	signal.signal(signal.SIGTERM, handler)
	signal.signal(signal.SIGINT, handler)

	# Run daily suggestion of new song
	Timer(scheduledTime(), runSuggestionJob, [ROOT, creds, slackSuggestionConnection]).start()

	# Begin listening loop
	while True:
		print("\n%s: Beginning new loop to listen for contact from Slack..." % datetime.today())
		messageChannel = None
		# Loop until a user has shared a Spotify link in an approved channel
		while not (messageChannel and urls):
			botWasBullied = False
			for slackMessage in slackConnection.rtm_read():
				messageChannel, urls, botWasBullied = f.slack.awaitContact(slackMessage, slackChannels, creds["spotify"]["urlbase"], slackRawBotId)
				if botWasBullied: 
					f.slack.sendMessage(slackConnection, messageChannel, f.messages.antiBullying(creds["slack"]["botId"]))
					continue
		trackIds = f.spotify.extractTrackIds(creds["spotify"]["urlbase"], urls)
		
		if trackIds:
			spotifyInstance = f.spotify.getSpotifyInstance(creds["spotify"]["username"], creds["spotify"]["id"], creds["spotify"]["secret"], creds["spotify"]["redirect"])
			
			if spotifyInstance:
				playlistId = f.spotify.getPlaylist(messageChannel, creds["channel-playlist-pairs"])
				playlistName, playlistUrl = f.spotify.getPlaylistInfo(spotifyInstance, creds["spotify"]["username"], playlistId)
				
				for trackId in trackIds:
					trackName = f.spotify.getTrackName(spotifyInstance, trackId)
					print trackId
					trackList = f.spotify.getPlaylistTracks(spotifyInstance, creds["spotify"]["username"], playlistId, f.spotify.getPlaylistTotalTracks(spotifyInstance, creds["spotify"]["username"], playlistId))
					if trackId in trackList:
						f.slack.sendMessage(slackConnection, messageChannel, f.messages.songAlreadyExists(trackName, playlistUrl, playlistName))
						continue
					f.spotify.postToPlaylist(spotifyInstance, creds["spotify"]["username"], playlistId, urls)
					f.slack.sendMessage(slackConnection, messageChannel, f.messages.songAdded(trackName, playlistUrl, playlistName))

except (KeyboardInterrupt):
	goodbye()