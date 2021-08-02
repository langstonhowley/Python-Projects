from spotify_connection import SpotifyConnection, Track
from spotipy.exceptions import SpotifyException
from astropy_connection import AstropyConnection
from credentials import fill_creds

import pymongo
from tqdm import tqdm

import sys
import os
import random
    

class Astrotune:

    def __init__(self):
        #Function to set environment variables
        fill_creds()

        #Get the Pymongo client
        client = pymongo.MongoClient(os.getenv('ASTROTUNE_DB_URI'))
        if client:
            try:
                spotify_username = sys.argv[1]
            except:
                spotify_username = input("Please enter your Spotify USERNAME >>> ")

            self.username = spotify_username
            print('Finding User {} in database...'.format(spotify_username))
            self.db = client['Astrotune']

            user = self.db.get_collection('User').find_one({'username':spotify_username})
           
            #TODO: Potentially make a new user but I think I'm only using this for now
            # and coding extraneous cases takes time :(
            if(not user):
                pass

            try:
                load_saved = sys.argv[2]
            except:
                load_saved = self.get_response('Update saved songs from your Spotify?', ['yes', 'y', 'no', 'n'], False)

            if(load_saved in ['yes', 'y']):
                self.spotify = SpotifyConnection(spotify_username)

                user_tracks = self.spotify.load_songs(-1)

                for i in tqdm(range(0, len(user_tracks))):
                    track = user_tracks[i]
                    self.db.get_collection('User').update_one(
                        {'username':spotify_username, 'saved_songs.name': {'$ne': track.name}}, 
                        {'$push': {'saved_songs': track.track_data}})
            else:
                self.spotify = SpotifyConnection(spotify_username)

            self.astro = AstropyConnection()
            self.q1()
        else:
            print('Couldn\'t connect to the database.')
            exit(1)

    def get_response(self, prompt = '', wanted_values = [], include_quit_cancel=True, cancel_fucntion=None):
        if(include_quit_cancel):
            wanted_values.extend(['c', 'cancel', 'q', 'quit'])

        while(True):
            value = input(prompt + f" ({wanted_values}) >>> ").strip().lower()

            if(value not in wanted_values):
                print(f"Accepted inputs -> {wanted_values}")
            else:
                if(include_quit_cancel and value in ['q', 'quit']):
                    exit(0)
                elif(include_quit_cancel and 
                    not cancel_fucntion is None and 
                    value in ['c', 'cancel']):
                    
                    cancel_fucntion()

                return value

    def q1(self) -> None :
        res = self.get_response('\n\nWould you like to search for [s]tars, [m]usic, [r]andom?', ['s', 'star', 'm', 'music', 'r', 'random'])

        if res in ['s', 'star']:
            designation = input('\nPlease type in the star\'s Gaia designation >>> ')
            object = self.db.get_collection('User').find_one({'star_catalog.gaia_designation': designation})

            if(not object == None):
                track = None

                for record in object['star_catalog']:
                    if(record['gaia_designation'] == designation):
                        track = self.spotify.get_track(track_id=record['track_id'])

                
                star = self.db.get_collection('Stars').find_one({'designation': designation}) 

                print('')
                print(f'{track}')
                print(f'{star}')
                self.q1()
            else:
                print(f"\n\t!!Could not find designation {designation} in your catalog!!")
                self.q1()
        elif res in ['r', 'random']:
            song_id = random.choice(self.db.get_collection('User').find_one({'username': self.username})['saved_songs'])['id']
            self.spotify.play(song_id)

            self.q1()
        else:
            self.q2()

    def q2(self):
        res = self.get_response('\nSearch by [a]rtist or [s]ong?', ['s', 'song', 'a', 'artist'], cancel_fucntion=self.q1)

        if res in ['a', 'artist']:
            self.q3()
        elif res in ['s', 'song']:
            pass

    def q3(self):
        saved = self.get_response('\nSearch in your [s]aved or from artist\'s [t]op songs?', ['s', 'saved', 't', 'top'], cancel_fucntion=self.q2)
        artist_name = input('Please type in the artist\'s name >>> ')

        if saved in ['s', 'saved']:

            artist = self.spotify.get_artist(query=artist_name, offset=0)
            artist_id = artist['id']

            print(artist_id)

a = Astrotune()

