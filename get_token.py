from urllib.parse import urlencode

App_ID = '51750980' 
OAuth_base_url = 'https://oauth.vk.com/authorize'
params = {
    'client_id': App_ID,
    'redirect_uri': 'https://oauth.vk.com/blank.html',
    'display': 'page',
    'scope': 'status, photos',
    'response_type': 'token'

}
oauth_url = f'{OAuth_base_url}?{urlencode(params)}'
print(oauth_url)
# user_id=822203161 # мой ВК номер


