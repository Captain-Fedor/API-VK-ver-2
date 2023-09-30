

class APClient:

    """ Методы Вконтакте"""

    Api_base_url = 'https://api.vk.com/method'
    def __init__(self, vk_token, ya_token):
        self.vk_token = vk_token
        # self.user_id = user_id
        self.ya_token = ya_token

    def get_common_params(self):
        return {
            'access_token': self.vk_token,
            'v': '5.131'
        }

    def get_userID(self):
        params = self.get_common_params()
        response = requests.get(f"{self.Api_base_url}/users.get", params=params).json()
        user_id = response.get('response')[0].get('id')
        return user_id

    def get_albums(self):
        params = self.get_common_params()
        folder_dict = {}
        response = requests.get(
            f"{self.Api_base_url}/photos.getAlbums", params=params)
        # print(response.json())
        for items in response.json().get('response', {}).get('items'):
            folder_dict.update({items['title']:items['id']})

        return folder_dict

    def get_profile_photos(self, folder_id):
        params = self.get_common_params()
        params.update({'owner_id': self.get_userID(), 'album_id': folder_id, 'photo_sizes': 1, 'extended': 1})
        response = requests.get(
            f"{self.Api_base_url}/photos.get", params=params)

        return response.json()

    def max_size_photo(self, number, folder_id): #number это порядковый номер фото в списке фоток
        max_height = 0
        user_photos = self.get_profile_photos(folder_id)
        photo_size_list = user_photos.get('response', {}).get('items')[number].get('sizes')  # список размеров одной фотки
        photo_date = user_photos.get('response', {}).get('items')[number].get('date')
        likes_count = user_photos.get('response', {}).get('items')[number].get('likes').get('count')
        for photo in photo_size_list:
            if photo['height'] > max_height:
                max_height = photo['height']
                max_size_url = str(photo['url'])
                photo_type = photo['type']
        return max_size_url, photo_type, photo_date, likes_count

    def list_of_photos_to_upload(self, folder_id):
        user_photos = self.get_profile_photos(folder_id)
        photo_count = user_photos.get('response', {}).get('count')
        lst = []
        for number in range(photo_count):
            lst.append(self.max_size_photo(number, folder_id))
        return lst

    def unix_to_timestamp(self, value):
        from datetime import datetime
        value = datetime.fromtimestamp(value)
        return value.strftime('%Y_%m_%d %Hhr %Mmin')

    def Json_file(self, folder_id):
        lst = self.list_of_photos_to_upload(folder_id)
        photos_list = []
        file_name_list = []
        photo_id_dict ={}
        # pprint(lst)
        for item in lst: #присвоение имени (если лайки дублируются до берется дата, если дата уже есть, то добавляем photo ver
            # item [2] id файла
            likes_count = item[3]

            if likes_count in file_name_list:
                file_name = self.unix_to_timestamp(item[2])

                if item[2] in photo_id_dict.keys():
                    photo_id_dict[item[2]] += 1
                    file_name = f'{file_name} photo {photo_id_dict[item[2]]}'

                else:
                    photo_id_dict[item[2]] = 1
            else:
                file_name = likes_count
                file_name_list.append(file_name)
                photo_id_dict[item[2]] = 1
            photos_list.append({'file_name': f'{file_name}.jpeg', 'size': item[1]})
        with open('photos_logу.json', 'w') as file:
            json.dump(photos_list, file)

        return photos_list

    def files_save_in_python(self, folder_id):
        lst = self.list_of_photos_to_upload(folder_id)
        for item in tqdm(range(len(lst)), desc='VK files download'):
            photo_url = lst[item][0]
            file_name = self.Json_file(folder_id)[item].get('file_name')
            response = requests.get(photo_url)
            sleep(0.3)
            with open(file_name, 'wb') as file:
                file.write(response.content)


    """Методы Яндекс"""

    ya_base_url = 'https://cloud-api.yandex.net'

    def ya_common_headers(self):
        return {'Authorization': f'OAuth {self.ya_token}'}


    # def folder_check(self, ya_folder): # проверяет наличие папки на яндекс диске
    #     url = 'https://cloud-api.yandex.net/v1/disk/resources'
    #     headers = self.ya_common_headers()
    #     params = {
    #         'path': '/',
    #         'fields': '_embedded.items.name',
    #     }
    #     response = requests.get(url, params=params, headers=headers).json()
    #     for item in response.get('_embedded').get('items'):
    #         if item['name'] == ya_folder:
    #             return True
    #         else:
    #             return False

        # return response
    def ya_folder(self, folder):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        params = {
            'path': folder

        }
        headers = self.ya_common_headers()
        response = requests.put(url, params=params, headers=headers)
        return response.status_code

    def ya_upload_link(self, folder, file_name):
        params = {'path': f'{folder}/{file_name}', 'overwrite': 'True'}
        headers = self.ya_common_headers()
        response = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload',
                                params=params, headers=headers).json()
        upload_link = response.get('href')
        return upload_link

    def ya_file_upload(self, folder, id_vk_folder):
        print("\033[32m {}".format('WARMING UP...'))
        # if self.folder_check(ya_folder) is False:
        self.ya_folder(folder)
        self.files_save_in_python(id_vk_folder)
        for item in tqdm(self.Json_file(folder_id), desc='YA files upload'):
            file_name = item['file_name']
            with open(file_name, 'rb') as file:
                response = requests.put(self.ya_upload_link(folder, file_name), files={'file': file})
            self.file_delete(file_name)
        print("\033[32m {}".format('COMPLETED!'))

    def file_delete(self,file): # удаление файла с компьютера после его закачки на яндекс
        os.remove(file)



if __name__ == '__main__':
    import requests
    from pprint import pprint
    from tqdm import tqdm
    from time import sleep
    import os
    import json
    import configparser


    App_ID = '51750980'
    # user_id = 822203161  # мой ВК номер

    # vk_token = 'vk1.a.LxMdqXQKSf4wLHVIYjtM71wyRJK9LUbxVQpcJHNQAX9MV85rQpYxxvcpKKTtXvKlp73p4eyGoxzrp_MHHjCAeCPC1HITGn7gxypxQBDJicfnQPCRX5Y1xmR5N-dSMR7MsQZSz89CMZN5b2mqFBFvDZ9SFpQ88FE0iIbfMRJq1ZzREr86SwyAxSswnzA5w48HjBlXsOTaW2zjfLEak58APg'
    # ya_token = 'y0_AgAAAABw6dhzAADLWwAAAADtGY1OPwhO7uLBTzCtL-I48NOLyPlvI0M'
    # ya_folder = 'VK ver5'
    # folder_id = 297310255 # папка qwert
    # number_of_photos = 5


    vk_token = input('INPUT VK TOKEN')
    ya_token = input('INPUT YANDEX TOKEN')
    config = configparser.ConfigParser()
    config.add_section('Settings')
    config.set('Settings', 'vk_token', vk_token)
    config.set('Settings', 'ya_token', ya_token)
    with open('config.ini', 'w') as file:
        config.write(file)
    config.read('config.ini')
    ya_token = config.get('Settings', 'ya_token')
    vk_token = config.get('Settings', 'vk_token')



    vk_client = APClient(vk_token, ya_token)

    vk_folder = input('INPUT FOLDER NAME IN VK PROFILE')
    folder_dict = vk_client.get_albums()
    while vk_folder not in folder_dict:
        print('FOLDER NOT IN VK PROFILE')
        vk_folder = input('INPUT FOLDER NAME')
    else:
        folder_id = folder_dict[vk_folder]
    number_of_photos = int(input('HOW MANY PHOTOS TO COPY?: '))
    count_photos = vk_client.get_profile_photos(folder_id).get('response', {}).get('count')

    if number_of_photos >= count_photos:
        print("\033[32m {}".format(f'ONLY {count_photos} PHOTOS WILL BE COPIED'))
    ya_folder = input('INPUT FOLDER NAME FOR YANDEX DISK: ')





    vk_client.ya_file_upload(ya_folder, folder_id)  # активация программы с казанием имени папки на Yandex и id папки вконтакте
    # vk_client.ya_folder(ya_folder)
    # vk_client.ya_upload_link()

    # print(vk_client.get_userID())
    # pprint(vk_client.get_albums())
    # pprint(vk_client.get_profile_photos(folder_id))
    # pprint(vk_client.list_of_photos_to_upload())
    # print(vk_client.Json_file())
    # vk_client.files_save_in_python()
    # vk_client.max_size_photo(0)..









