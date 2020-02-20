# Box API Class
# @author: Edgar Han

import logging,requests
import time
import secrets

class Box():
    url = "https://api.box.com"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    client_id = ''
    client_secret = ''

    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {'Authorization': 'Bearer {}'.format(self.access_token)}

    def get_token(self):
        url = '{}/oauth2/token'.format(self.url)
        data = {
                'client_id': self.client_id,
                'grant_type': 'authorization_code'
                }
        response = requests.post(url,
                                 headers=self.headers,
                                 data=data)
        json_response = response.json()
        print(json_response)
        token = json_response['access_token']
        logging.debug('token {}'.format(token))
        return token

    def get_files_info(self):
        url = '{}/2.0/files'.format(self.url)
        response = requests.get(url, headers=self.headers)
        json_response = response.json()
        return json_response

    def get_recent_items(self):
        url = '{}/2.0/recent_items'.format(self.url)
        response = requests.get(url, headers=self.headers)
        json_response = response.json()
        return json_response

    def list_folder_items(self, folder_id):
        url = '{}/2.0/folders/{}/items'.format(self.url, str(folder_id))
        response = requests.get(url, headers=self.headers)
        json_response = response.json()
        return json_response

    def get_folder_info(self, folder_id):
        url = '{}/2.0/folders/{}'.format(self.url, str(folder_id))
        response = requests.get(url, headers=self.headers)
        json_response = response.json()
        return json_response

    def list_collections(self):
        url = '{}/2.0/collections'.format(self.url)
        r = requests.get(url, headers=self.headers)
        jr = r.json()
        return jr



### quick test
