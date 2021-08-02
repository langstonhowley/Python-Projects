import time
import spotipy
import spotipy.util as util

class Track:

	def __init__(self):
		self.id = ''
		self.name = ''
		self.artist_id = []
		self.artist_name = []
		self.album_id = ''
		self.album_name = ''
		self.features = {}
		self.track_data = {}


	def from_track_data(td):
		track = Track()
		track.id = track.track_data['id'] = td['id']
		track.name = track.track_data['name'] = td['name']

		track.track_data['album'] = {}
		track.track_data['album']['artists'] = []

		for artist in td['album']['artists']:
			track.artist_id.append(artist['id'])
			track.artist_name.append(artist['name'])

			track.track_data['album']['artists'].append({'id': artist['id'], 'name': artist['name']})

		
		track.album_id = track.track_data['album']['id'] = td['album']['id']
		track.album_name =  track.track_data['album']['name'] = td['album']['name']

		track.track_data['features'] = {}

		return track

	def set_features(self, features):
		self.features = features
		self.track_data['features'] = features
	
	def from_json(json):
		track  = Track()
		track.id = json['id']
		track.name = json['name']
		track.artist_name = json['artists']['name']
		track.artist_id = json['artists']['id']
		track.album_name = json['album_name']
		track.album_id = json['album_id']
		track.features = json['features']

		return track

	def as_json(self):
		payload = {
			'id': self.id,
			'name': self.name,
			'artists': {
				'name': self.artist_name,
				'id': self.artist_id
			},
			'album_name': self.album_name,
			'album_id': self.album_id,
			'features': self.features
		}

		return payload
		
	def __repr__(self):
		return f'''{self.name} by {self.artist_name} - {self.album_name}'''	


class SpotifyConnection:
	
	def __init__(self, username):		
		print('Getting Spotify access token...')

		scope = '''user-library-read
		playlist-read-collaborative 
		playlist-read-private 
		streaming 
		user-modify-playback-state
		user-read-playback-state
		user-read-recently-played
		user-read-currently-playing
		user-read-private'''.replace('\n', ' ').replace('\t', '')

		try:
			self.access_token = util.prompt_for_user_token(username, scope)

			self.sp = None
			self.user = None

			if self.access_token:
				self.sp = spotipy.Spotify(auth=self.access_token)

				me = self.sp.me()
				name = me['display_name']
				id = me['id']

				while True:
					try:
						device = self.sp.devices()['devices'][0]
						break
					except Exception:
							print('Please open a Spotify seesion either in a browser or on the app...')
							time.sleep(1)
						
				self.user = {'name': name, 'id': id, 'device': device}

				print('Got access token for user ' + self.user['name'])
			else:
				print("Can't get token for", username)
		except Exception as e:
			print("Error in Spotify init: ", e)
			exit(1)

	def load_songs(self, num_songs, offset=0):
		saved = []

		if(num_songs > 0):
			tracks_per = min(50, num_songs)
		else:
			tracks_per = 50
		tracks_recv = [None]

		i = offset

		try:
			if(num_songs > 0):
				print('Getting {} saved songs from Spotify...'.format(num_songs-offset))
			else:
				print('Getting all saved songs from Spotify...')

			while (len(tracks_recv) > 0 and (i < num_songs or num_songs == -1)):
				tracks_recv.clear()

				tracks_recv = self.sp.current_user_saved_tracks(limit=tracks_per, offset=i)['items']
				#print(str(len(tracks_recv)) + ' tracks received')

				for idx, item in enumerate(tracks_recv):
					track = Track.from_track_data(item['track'])
					#print(self.sp.audio_features([track.id]))
					track.set_features(self.sp.audio_features([track.id])[0])

					print('Loaded {}'.format(track))
					saved.append(track)
				i += tracks_per
		except spotipy.exceptions.SpotifyException as e:
			print('Refreshing access token because: {}'.format(e))
			self.refresh_token()
			saved.extend(self.load_songs(num_songs,offset=i))

			if(i > 0):
				print('Got {} songs from {}\'s saved songs'.format(len(saved), self.user['name']))

			return saved
		except Exception as e:
			print('Encountered error: {}'.format(e))

			if(i > 0):
				print('Got {} songs from {}\'s saved songs'.format(len(saved), self.user['name']))

			return saved

		if(i > 0):
			print('Got {} songs from {}\'s saved songs'.format(len(saved), self.user['name']))

		return saved


	def refresh_token(self):
		credentials = spotipy.oauth2.SpotifyOAuth(token=self.access_token)
		self.access_token = credentials.get_access_token(as_dict=True)
		return self.access_token


	def get_track(self, query=None, offset=None, track_id=None) -> Track:
		if(query == None and offset == None and not track_id == None):
			track_data = self.sp.track(track_id)
			return Track.from_track_data(track_data)
		elif(not (query == None and offset == None and not track_id == None)):
			return Track.from_track_data(self.sp.search(query,limit=1,type='track',offset=offset)['tracks']['items'][0])
		else:
			raise ValueError('Arguments supplied incorrectly: {}, {}, {}'.format(query, offset, track_id))

	def get_artist(self, query=None, offset=None, artist_id=None):
		if(query == None and offset == None and not artist_id == None):
			return self.sp.artist(artist_id)
		elif(not (query == None and offset == None and not artist_id == None)):
			return self.sp.search(query,limit=1,type='artist',offset=offset)['artists']['items'][0]
		else:
			raise ValueError('Arguments supplied incorrectly: {}, {}, {}'.format(query, offset, artist_id))

	def get_q(self, item, query='', offset=0):
		if item in ['artist','a']:
			res = self.sp.search(query,limit=1,type='artist',offset=offset)
			return res['artists']['items'][0]
		elif item in ['track', 't']:
			res = self.sp.search(query,limit=1,type='track',offset=offset)
			return Track.from_track_data(res['tracks']['items'][0])


	def play(self, track_id):
		track = 'spotify:track:' + track_id
		self.sp.start_playback(uris=[track], device_id=self.user['device']["id"])
		

