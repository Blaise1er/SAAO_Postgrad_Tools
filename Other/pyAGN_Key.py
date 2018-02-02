# The purpose of this script is to make it easy to filter data from the AGN Key website, it is too cluttered for my liking.

# First let us import some modules

import pandas as pd
from bs4 import BeautifulSoup
from astropy import coordinates as coords
from astroquery.sdss import SDSS
import numpy as np
import requests

try:
    import plotly as py
    import plotly.graph_objs as go
except ImportError:
    print('plotly not installed, try - pip install plotly')
    sys.exit()

# The URL of the AGN key website

post_url = 'http://dark.physics.ucdavis.edu/~hal/cgi-bin/agnagent/agnkeymain.cgi'


# The actual work is done here

with requests.Session() as s:
    # login to AGN Key website, unfortunately you cannot test this since you do not have a password and username.
    response = s.post(post_url, auth = ('your_username', 'your_password'))

    # If the status code is 200, continue
    if response.status_code == requests.codes.ok:
        # Pass response to BeautifulSoup to deal with the HTML document
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Empty lists to store data, these are the column names from the website in order
        agn_names, ra, dec, agn_type, z, n_nights, last_obs = [], [], [], [], [], [], []
        
        # Now use the magic of BeautifulSoup to handle the HTML, skip the header and the last two rows as they are
        # not important
        for tr in soup.find_all('tr')[1:-2]:
            td = tr.find_all('td')
            
            agn_names.append(td[0].text)
            ra.append(td[1].text)
            dec.append(td[2].text)
            agn_type.append(td[3].text)
            z.append(td[4].text)
            n_nights.append(td[5].text)
            last_obs.append(td[6].text)

        # Convert to arrays
        agn_names = np.array(agn_names)
        ra = np.array(ra)
        dec = np.array(dec)
        agn_type = np.array(agn_type)
        z = np.array(z)
        n_nights = np.array(n_nights)
        last_obs = np.array(last_obs)
            
        # Create dataframe so that the data is nicely formatted and easy to read

        data = {
            'AGN': pd.Series(agn_names),
            'RA': pd.Series(ra),
            'DEC': pd.Series(dec),
            'Type': pd.Series(agn_type),
            'z': pd.Series(z),
            'N_nights': pd.Series(n_nights),
            'Last_Obs': pd.Series(last_obs)
            }

        df = pd.DataFrame(data)

        # Change data type of columns
        # If 'coerce', then invalid parsing will be set as NaN
        df[['RA','DEC', 'z', 'N_nights']] = df[['RA','DEC', 'z', 'N_nights']].apply(pd.to_numeric, errors = 'coerce')
        df[['AGN','Type', 'Last_Obs']] = df[['AGN','Type', 'Last_Obs']].astype(str)
        
        # Now we can start querying the table
        subset_agn = df[df['z'] < 0.1]  # select all objects with redshift of z < 0.1
        
        #print(subset_agn)
        
        # To observe with SALT, the declination must lie between -76 and +11.25
        dec_start, dec_end = -76.0000, 11.25
        mask = (subset_agn['DEC'] > dec_start) & (subset_agn['DEC'] < dec_end)
        visible_with_salt = subset_agn[mask] 
        
        #print(visible_with_salt)
        
        # You can take it further and plot the SDSS spectrum by using astroquery
        target_agn = 'PG1244'
        search_string = visible_with_salt[visible_with_salt['AGN'].str.contains(target_agn)]

        target_ra = search_string['RA']
        target_dec = search_string['DEC']

        pos = coords.SkyCoord(target_ra, target_dec, unit = 'deg')
        xid = SDSS.query_region(pos, spectro = True)
        
        # Plot if match is found
        if xid is not None:
            sp = SDSS.get_spectra(matches = xid)
        
            trace0 = go.Scatter(
                        x = 10. ** sp[0][1].data['loglam'],
                        y = sp[0][1].data['flux'],
                        name = target_agn,
                        line = dict(
                                dash = 'line'
                                )
                        )
            data = [trace0]
            layout = dict(xaxis = dict(title = 'Wavelength'), yaxis = dict(title = 'Flux'), showlegend = True)
            fig = dict(data = data, layout = layout)
            py.offline.plot(fig, filename = 'temp.html')


