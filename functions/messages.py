def songAdded(trackName, playlistUrl, playlistName):
	return "I've added _%s_ to the Spotify playlist, <%s|%s>. :boom:" % (trackName, playlistUrl, playlistName)

def songAlreadyExists(trackName, playlistUrl, playlistName):
	return "_%s_ is a cool song, but it's already in your playlist, <%s|%s>. I ain't doing nothing." % (trackName, playlistUrl, playlistName)

def antiBullying(botId):
	return "Bots have feelings, too, y'know. Bullying makes <@%s> :cry:." % botId

def songRecommendation(url, approvalsRequired, rejectionsRequired, expiration):
	return "Hey! I took a look at your playlist, and I think you'd enjoy this song: <%s>. If %s room member%s react%s to this suggestion with a :+1:, I'll add it to your playlist. If %s room member%s react%s with a :-1:, I'll scrap it. You have until %s to respond!" % (url, approvalsRequired, "s" if approvalsRequired > 1 else "", "" if approvalsRequired > 1 else "s", rejectionsRequired, "s" if rejectionsRequired > 1 else "", "" if rejectionsRequired > 1 else "s", expiration)

def couldNotGetSong():
	return "Sorry! I wasn't able to get a recommendation for your playlist today. Maybe tomorrow!"