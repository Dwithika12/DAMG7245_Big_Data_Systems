import base64
import glob
import io
import json
import os
import urllib.parse
from os import walk

# import cv2
# import gcsfs
import h5py
import imageio
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import tensorflow as tf
import uvicorn
from fastapi import Body, Depends, FastAPI, Request
# from display.display import get_cmap
from fastapi.responses import FileResponse, JSONResponse
from geopy import distance
from PIL import Image
from starlette.responses import StreamingResponse

from app.auth.jwt_bearer import JWTBearer
from app.auth.jwt_handler import signJWT, decode_JWT
from app.model import PostSchema, UserLoginSchema, UserSchema


"""
Reading and writing data to GCS

https://cloud.google.com/appengine/docs/standard/python/googlecloudstorageclient/read-write-to-cloud-storage

Using Google Firestore for storing data

https://cloud.google.com/appengine/docs/standard/python3/using-cloud-datastore

"""



MODEL_PATH = '../model/mse_model_nowcast.h5'

model_gcs = h5py.File(MODEL_PATH, 'r')
new_model = tf.keras.models.load_model(model_gcs, compile=False, custom_objects={"tf": tf})

# load CSV file
csv_path = '../catalog_storm_vil_2019_new.csv'

catalog_2events = pd.read_csv(csv_path)


# http://127.0.0.1:8000

app = FastAPI()


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )



################### Download H5 files for selected Event Id only ##########################################


def get_filename_index(event_id):
    catlog = pd.read_csv("https://raw.githubusercontent.com/MIT-AI-Accelerator/eie-sevir/master/CATALOG.csv")
    filtered = pd.DataFrame()
    for i in event_id:
        filtered = pd.concat([filtered, catlog[catlog["event_id"] == int(i)]])
        filename = filtered['file_name'].unique()
        fileindex = filtered['file_index'].unique()
    print("We have got the locations, Lets Download the files")
    return filename, fileindex


# def download_hf(filename):
#     resource = boto3.resource('s3')
#     resource.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
#     bucket = resource.Bucket('sevir')

#     for i in range(len(filename)):
#         filename1 = "data/" + filename[i]
#         print("Downloading", filename1)
#         bucket.download_file(filename1, "SEVIR/" + filename[i].split('/')[2])


def One_Sample_HF(directory, fileindex, location):
    filenames = next(walk(directory), (None, None, []))[2]  # [] if no file
    for i in range(len(filenames)):
        print(directory + filenames[i])
        if filenames[i] == '.DS_Store' or filenames[i] == '.gitkeep':
            continue
        with h5py.File(directory +'/'+ filenames[i], 'r') as hf:
            image_type = filenames[i].split('_')[1]
            # if image_type == "IR107":
            #     event_id = hf['id'][int(fileindex[1])]
            #     IR107 = hf['ir107'][int(fileindex[1])]
            if image_type == "VIL":
                VIL = hf['vil'][int(fileindex)]
            # if image_type == "IR069":
            #     IR069 = hf['ir069'][int(fileindex[2])]
            # if image_type == "VIS":
            #     VIS = hf['vis'][int(fileindex[0])]
    
    hf1 = h5py.File('../data/'+location+'/'+location+ '_filtered_data.h5', 'w')
        
    hf1.create_dataset('vil', data=VIL)
        
    # hf1.close()
    # hf1.create_dataset('vis', data=VIS)
    # hf1.create_dataset('IR107', data=IR107)
    # hf1.create_dataset('IR069', data=IR069)
    print("downloded")


def testdata(dir):
    rank=0
    size=1 
    end=None
    s = np.s_[rank:end:size]
    MEAN=33.44 
    SCALE=47.54
    # file_name = data_model['images_path']
    with h5py.File(dir) as hf:
        x_test = hf['vil'][s]
    x_test = (x_test.astype(np.float32)-MEAN)/SCALE
    # return 1st 13 images 
    x_test = x_test.reshape(1, 384, 384, 49)
    x_test_now = x_test[:, :, :, :13]
    return x_test_now

def get_lat_long(location):

    """
    Python script that does not require an API key nor external libraries 
    you can query the Nominatim service which in turn queries 
    the Open Street Map database.

    For more information on how to use it see
    https://nominatim.org/release-docs/develop/api/Search/

    """
    address = location
    url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) +'?format=json'

    response = requests.get(url).json()
    # print(response[0]["lat"])
    # print(response[1]["lon"])
    return response[0]["lat"], response[1]["lon"]


# def get_data_from_google_cloud_storage():

#     storage_client = storage.Client()
#     print("Downloading the data from Google Cloud Storage")
#     bucket_name = 'sevir'
#     file_name = 'data/' + data_model['images_path']
#     print(file_name)
#     blob = storage_client.bucket(bucket_name).blob(file_name)
#     blob.download_to_filename('data/' + data_model['images_path'])
#     print("Downloaded the data from Google Cloud Storage")



def nearest_location(lat, lon, flag, location):
    # Returns the row from the combined csv that has 
    # least distance from the given lat and lon
    path = '../data'+'/'+location+'/'

    # Check whether the specified path exists or not
    isExist = os.path.exists(path)

    if not isExist:
      # Create a new directory because it does not exist 
      os.makedirs(path)
    catalog_2events['distance'] = catalog_2events.apply(lambda row: distance.distance((lat, lon), (row['LATITUDE'], row['LONGITUDE'])).km, axis=1)
    nearest_loc_vil = catalog_2events.loc[catalog_2events['img_type'] == 'vil']
    nearest_loc = nearest_loc_vil.loc[nearest_loc_vil['distance'].idxmin()]
    top_min_distances = nearest_loc_vil.loc[nearest_loc_vil['distance'].nsmallest(5).index]
    top_min_distances.to_csv('/home/shinde_priyanka_15ee1156/sevir/data'+'/'+location+'/'+location+'_top_5_min_distances.csv')
    if nearest_loc['distance'] >= 100:
        flag == True
    print(nearest_loc)
    return nearest_loc, flag

def read_data_local(filename, rank=0, size=1, end=None, dtype=np.float32, MEAN=33.44, SCALE=47.54):
    
    s = np.s_[rank:end:size]
    with h5py.File(filename, mode='r') as hf:
        x_test  = hf['vil'][s]
    x_test = (x_test.astype(dtype)-MEAN)/SCALE
    
    return x_test



"""
1. model loading
2. predict
3. save 12 images
4. Save the input image for that 

"""


@app.get("/nowcast/{img_Id}")
async def predict_img(img_Id: int):
    """
    **Pass Image Id to show 1 out of 12 images!!**
    """

    # create_nowcast(1)
    str1 = ""
    path = '../images/'

    # with h5py.File('y_pred.h5', 'r') as hf:
    #     # plt.imshow(hf['pred'][0][:,:,11])
    #     print("Image " + str(img_Id) + "selected")
    #     str1 = str(hf['pred'][0][:, :, img_Id].shape)
    #     image_data = hf['pred'][0][:, :, img_Id]

    #     # for i in range(0, 11):
    #     #     name = path + "test" +  str(i) + '.png'
    #     #     plt.imsave(name, hf['pred'][0][:,:,i])
    #     plt.imsave("test.png", image_data)

    filepath = os.path.join(path, "test" + str(img_Id) +".png")
    if os.path.exists(filepath):
        return FileResponse(filepath)

    return {"error": "File not found!"}


def verify_jwt(jwtoken: str):
        isTokenValid : bool = False
        try:
            payload = decode_JWT(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid

# 1 Get a Nowcast for the location
# A request can be made to API only if the user is logged in and JWT token is valid
api_count = 2

@app.get("/weatherviz/{location}", tags=["Nowcasting"])
async def filter_nowcast(location: str, next_nearest: str):
    """
    **Get Nowcast Images for the exact or nearest location in SEVIR**

    """
    # isTokenValid = verify_jwt(jwtoken)
    # print(isTokenValid)
    # if verify_jwt(jwtoken):
    ## Calculate API calls left - decrement
    # api_df = pd.read_csv('../data/sevir_users.csv')
    # api_count = api_df['api_count']
    # api_count = api_count - 1
    # api_df['api_count'] = api_count
    # api_df.to_csv('../data/sevir_users.csv')
    if api_count > 0:
        flag = False
        norm = {'scale': 47.54, 'shift': 33.44}
        location_lat_long = get_lat_long(location)
        print(location_lat_long)
        # gives me the row in catalog with nearest location
        nearest_location_catalog, not_nearest = nearest_location(location_lat_long[0], location_lat_long[1], flag, location.strip().split(',')[0])
        # print("FLAG VALUE", not_nearest)
        # not_nearest flag stores if the nearest datapoint is within 100 kms of user input location
        # if flag is true -> nearest location is outside 100 kms of user input location

        event_file_name = nearest_location_catalog['file_name']
        event_file_index = nearest_location_catalog['file_index']
        event_id_nearest = nearest_location_catalog['event_id']

        h5_files_path = '../data/sevir-data/'
        One_Sample_HF(h5_files_path, event_file_index, location.strip().split(',')[0])

        # x_test = read_data_local('filtered_data.h5', end=50)
        filtered_path = '../data'+'/'+location.strip().split(',')[0]+'/'+location.strip().split(',')[0]+"_filtered_data.h5"
        filtered_data_path = filtered_path
        # testdata fn return reshaped -- (1, 384, 384, 49) --  1st 13 images
        x_test = testdata(filtered_data_path)



        # x_test = x_test.reshape(1, 384, 384, 49)
        # x_test_now = x_test[:, :, :, :13]


        y_preds = []

        yp = new_model.predict(x_test)

        if isinstance(yp, (list,)):
            yp = yp[0]
        y_preds.append(yp * norm['scale'] + norm['shift'])
        y_preds_path = '../data'+'/'+location.strip().split(',')[0]+'/'+location.strip().split(',')[0]+"_y_pred.h5"
        with h5py.File(y_preds_path, 'w') as data:
            data['pred'] = y_preds[0]

        # Read the y pred h5 file
        images_path = '../images/'+location.strip().split(',')[0]+'/'
        images_path = '../images/'+location.strip().split(',')[0]+'/'

        # Check whether the specified path exists or not
        isExist = os.path.exists(images_path)

        if not isExist:
          # Create a new directory because it does not exist 
          os.makedirs(images_path)
        with h5py.File(y_preds_path, 'r') as hf:
            # plt.imshow(hf['pred'][0][:,:,11])
            # print("Image " + str(img_Id) + "selected")
            # str1 = str(hf['pred'][0][:, :, img_Id].shape)
            for i in range(0, 12):
                name = images_path + "test" +  str(i) + '.png'
                plt.imsave(name, hf['pred'][0][:,:,i])
                # image_data = hf['pred'][0][:, :, 1]
                # plt.imsave("test.png", image_data)
            # Create a GIF out of images

            filenames = glob.glob(images_path+'test*.png')
            images = []
            for filename in filenames:
                images.append(imageio.imread(filename))
            imageio.mimsave(images_path+"nowcast"+ '.gif', images)
        # if nearest_location_catalog['distance'] >= 100:
        #     return {"data": None, "message": "No nearest location found within 100 kms of your location"}
        nowcast_images_path = '../images/'+location.strip().split(',')[0]+'/'+"nowcast.gif"
        # Based on next_nearest variable -> yes/no show message or images
        if next_nearest.lower() == "yes":
            # filepath = os.path.join(nowcast_images_path, location.strip().split(',')[0]+"nowcast.gif")
            if os.path.exists(nowcast_images_path):
                return FileResponse(nowcast_images_path)

            return {"error": "File not found!"}

        else:

            return {"message": "No nearest location found within 100 kms of your location"}
    else:
        return {"message": "You have exceeded Max. API Calls!"}

        

users = []
# 2 User Signup
@app.post("/users/signup", tags=["user"])
def user_signup(user: UserSchema = Body(default=None)):
    users.append(user)
    return signJWT(user.email)

def check_user(data: UserLoginSchema):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
        else:
            return False

# 3 User Login
@app.post("/users/login", tags=["user"])
def user_login(data: UserLoginSchema = Body(default=None)):
    if check_user(data):
        print(check_user(data))
        return signJWT(data.email)
    else:
        return {"message": "Invalid credentials"}

# 4 User list 
@app.get("/users", tags=["users"])
def get_users():
    return {"data": users}