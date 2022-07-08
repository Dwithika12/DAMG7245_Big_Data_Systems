import h5py
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from PIL import Image
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.patches as patches
import pandas as pd
import os
from display.display import get_cmap
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import cv2
import subprocess
from starlette.responses import StreamingResponse
import io

frozen_file_path  = '/Users/priyankashinde/Desktop/neurips-2020-sevir-master/models/mse_model_nowcast.h5'
print("Loading Model")
new_model = tf.keras.models.load_model(frozen_file_path,compile=False,custom_objects={"tf": tf})

from fastapi import FastAPI, Request
import uvicorn
app = FastAPI()

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )

from readers.nowcast_reader import read_data
x_test,y_test = read_data('nowcast_testing.h5',end=50)

catalog_2events = pd.read_csv("CATALOG.csv")


def create_nowcast(idx):
    norm = {'scale':47.54,'shift':33.44}
    hmf_colors = np.array( [
        [82,82,82], 
        [252,141,89],
        [255,255,191],
        [145,191,219]
    ])/255

    # Model that implements persistence forecast that just repeasts last frame of input
    class persistence:
        def predict(self,x_test):
            return np.tile(x_test[:,:,:,-1:],[1,1,1,12])

    def plot_hit_miss_fa(ax,y_true,y_pred,thres):
        mask = np.zeros_like(y_true)
        mask[np.logical_and(y_true>=thres,y_pred>=thres)]=4
        mask[np.logical_and(y_true>=thres,y_pred<thres)]=3
        mask[np.logical_and(y_true<thres,y_pred>=thres)]=2
        mask[np.logical_and(y_true<thres,y_pred<thres)]=1
        cmap=ListedColormap(hmf_colors)
        ax.imshow(mask,cmap=cmap)

    
        


    def visualize_result(models,x_test,y_test,idx,labels):
        fs=10
        cmap_dict = lambda s: {'cmap':get_cmap(s,encoded=True)[0],
                            'norm':get_cmap(s,encoded=True)[1],
                            'vmin':get_cmap(s,encoded=True)[2],
                            'vmax':get_cmap(s,encoded=True)[3]}
        
        pers = persistence().predict(x_test[idx:idx+1])
        pers = pers*norm['scale']+norm['shift']
        x_test = x_test[idx:idx+1]
        y_test = y_test[idx:idx+1]*norm['scale']+norm['shift']
        y_preds=[]
        for i,m in enumerate(models):
            yp = m.predict(x_test)
            if isinstance(yp,(list,)):
                yp=yp[0]
            y_preds.append(yp*norm['scale']+norm['shift'])
            with h5py.File("y_pred1.h5", 'w') as data:
                data['pred'] = y_preds[0]

    visualize_result([new_model],x_test,y_test,idx,labels=['MSE'])

# get endpoint -> state

"""
1. model loading
2. predict
3. save 12 images
4. Save the input image for that 

"""

# @app.get("/nowcast/{statea}")
# async def filter_nowcast(statea : str):

#     # x_test,y_test = read_data('nowcast_testing.h5',end=50)
#     # q = create_testData(state)
#     w, c = "", ""
#     t, v = "", ""
#     if statea == "MISSOURI":
#         w = catalog_2events['event_type_y'].loc[catalog_2events['state']=='MISSOURI']
#         t = catalog_2events['event_narrative'].loc[catalog_2events['state']=='MISSOURI']
#         return {"Event Type": w, "Event Narrative": t}
    
#         # subprocess.call(["/Users/priyankashinde/Desktop/neurips-2020-sevir-master/notebooks/event1.sh"])
#     # event id 858968
#     elif statea == "MINNESOTA":
#         c = catalog_2events['event_type_y'].loc[catalog_2events['state']=='MINNESOTA']
#         v = catalog_2events['event_narrative'].loc[catalog_2events['state']=='MINNESOTA']
#         print(c, v)
#         return {"Event Type": c, "Event Narrative": v}

        
    

    # create_nowcast(1)
    # str1 = ""
    # path = "/Users/priyankashinde/Desktop/neurips-2020-sevir-master/notebooks/"
    # # catalog_path = "/Users/priyankashinde/Desktop/neurips-2020-sevir-master/notebooks/combined_storm_data.csv"

    # # catalog_df = pd.read_csv(catalog_path)


    # with h5py.File('y_pred1.h5','r') as hf:
    #     # plt.imshow(hf['pred'][0][:,:,11])
    #     # print("Image " + str(img_Id) + "selected")
    #     # str1 = str(hf['pred'][0][:,:,img_Id].shape)
    #     # image_data = hf['pred'][0][:,:,:]
    #     for i in range(0, 11):
    #         name = path + "test" +  str(i) + '.png'
    #         plt.imsave(name, hf['pred'][0][:,:,i])

    #     filepath = os.path.join(path, "test.png")
    #     if os.path.exists(filepath):
    #         return FileResponse(filepath)
        
    #     return {"error": "File not found!"}


@app.get("/nowcast/{img_Id}")
async def predict_img(img_Id : int):
    """
    **Pass Image Id to show 1 out of 12 images!!**
    """

    create_nowcast(1)
    str1 = ""
    path = "/Users/priyankashinde/Desktop/neurips-2020-sevir-master/notebooks/"

    with h5py.File('y_pred1.h5','r') as hf:
        # plt.imshow(hf['pred'][0][:,:,11])
        print("Image " + str(img_Id) + "selected")
        str1 = str(hf['pred'][0][:,:,img_Id].shape)
        image_data = hf['pred'][0][:,:,img_Id]

        # for i in range(0, 11):
        #     name = path + "test" +  str(i) + '.png'
        #     plt.imsave(name, hf['pred'][0][:,:,i])
        plt.imsave("test.png", image_data)

        filepath = os.path.join(path, "test.png")
        if os.path.exists(filepath):
            return FileResponse(filepath)
        
        return {"error": "File not found!"}

    
@app.get("/weatherviz/{state}")
async def filter_nowcast(state : str):
    """
    **Get weather visualization stats based on state selection!**
    
    """
    w, c = "", ""
    t, v = "", ""

    if state == "MISSOURI":
        w = catalog_2events['event_type_y'].loc[catalog_2events['state']=='MISSOURI']
        t = catalog_2events['event_narrative'].loc[catalog_2events['state']=='MISSOURI']
        return {"Event Type": w, "Event Narrative": t}
    
    elif state == "MINNESOTA":
        c = catalog_2events['event_type_y'].loc[catalog_2events['state']=='MINNESOTA']
        v = catalog_2events['event_narrative'].loc[catalog_2events['state']=='MINNESOTA']
        print(c, v)
        return {"Event Type": c, "Event Narrative": v}


    