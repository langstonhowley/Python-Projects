# astropy imports
import random
from astropy import coordinates
from astropy.table import QTable
import astropy.units as u
from astropy.units.equivalencies import parallax
from astroquery.gaia import Gaia
from astroquery.simbad import Simbad

from os.path import exists, dirname
from tqdm import tqdm

class AstropyConnection:
    def __init__(self):
        query = '''SELECT TOP 50000 designation, ra, dec, parallax, pmra, pmdec, radial_velocity,
        phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag, radius_val, lum_val
        FROM gaiadr2.gaia_source
        WHERE parallax_over_error > 5 AND
            parallax > 10 AND
            radial_velocity IS NOT null AND
            radius_val IS NOT null
        ORDER BY radius_val DESC
        '''

        self.catalouge = []
        self.active_catalouge = []
        self.star_track_connections = {}

        gaia_file = dirname(__file__) + '/gaia_data.fits'
        if(exists(gaia_file)):
            data = QTable.read(gaia_file)
        else:
            job = Gaia.launch_job(query, verbose=True, 
                output_format='fits', dump_to_file=True, output_file=gaia_file)
            data = job.get_results()

        distances = coordinates.Distance(parallax=u.Quantity(data['parallax']*u.mas))

        for x in tqdm(range(0,len(data),1), desc="Loading Internal Star Catalouge", ncols=100):
            obj = dict(data[x])

            for key, value in obj.items():
                #print (key, value)
                try:
                    obj[key] = float(value)
                except:
                    pass

            obj['distance'] = float(distances[x].value)

            self.catalouge.append(obj)

    def star_from_track_features(self, tf):
        acousticness = float(tf['acousticness'])
        danceability = float(tf['danceability'])
        energy = float(tf['energy'])
        instrumentalness = float(tf['instrumentalness'])
        loudness_reversed = 60 + float(tf['loudness'])
        tempo = float(tf['tempo'])
        valence = float(tf['valence']) #happiness
        id = tf['id']


        while True:        
            rand_star = random.choice(self.catalouge)

            if rand_star['designation'] not in self.star_track_connections:
                self.star_track_connections[rand_star['designation']] = id
                break
                
        #print(self.star_track_connections)
        return rand_star
