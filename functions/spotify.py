import math, spotipy, spotipy.util as util

def getPlaylist(channel, pairs):
	for pair in pairs:
		if channel == pair["channel"]:
			return pair["playlist"]
	return None

def extractTrackIds(urlBase, urls):
	trackIds = []
	for url in urls:
		trackIds.append("spotify:track:" + url.replace(urlBase,""))
	return trackIds

def getSpotifyInstance(username, clientId, clientSecret, redirect, scope="playlist-modify-public"):
	token = util.prompt_for_user_token(username, scope, clientId, clientSecret, redirect)
	if token: 
		spotify = spotipy.Spotify(auth=token)
		spotify.trace = False
		return spotify
	return None

def getPlaylistTotalTracks(spotify, username, playlistId):
	results = spotify.user_playlist_tracks(username, playlistId, "total")
	return results["total"]

def getTrackName(spotify, trackId):
	results = spotify.track(trackId)
	return results["name"]

def getPlaylistTracks(spotify, username, playlistId, totalTracks, trackIds=[]):
	runsNeeded = int(math.ceil(totalTracks / 100.0))
	for i in range(0, runsNeeded):
		results = spotify.user_playlist_tracks(username, playlistId, offset=100*i, fields="items(track(uri))")
		for j in range(0, len(results["items"])):
			trackIds.append(results["items"][j]["track"]["uri"])
	return trackIds

def postToPlaylist(spotify, username, playlistId, trackIds):
	results = spotify.user_playlist_add_tracks(username, playlistId, trackIds)

def buildPlaylistUrl(username, playlistId):
	return "https://open.spotify.com/user/%s/playlist/%s" % (username, playlistId)

def getPlaylistInfo(spotify, username, playlistId):
	results = spotify.user_playlist(username, playlistId, "name")
	return results["name"], buildPlaylistUrl(username, playlistId)

