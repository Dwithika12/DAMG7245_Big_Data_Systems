# DAMG7245-Assignment-3-Repo



[CODELAB LIVE DOCUMENT](https://codelabs-preview.appspot.com/?file_id=1t8N4ZBmDzJN7NPZ1DF30mFVNh0J_2KRChuQmPJmODAE#2) 🚀

### Team Members

| NUID | Team Member       |
|:-----:|---------------|
| 001021288    | Kshitij Zutshi |
| 001524484      | Priyanka Dilip Shinde              |
| 002114630      | Dwithika Shetty              |

## Tasks:

### Part 1: Design the Client and parameter file

1. Get familiar with the Gretel design and run the tutorials [OPEN](https://github.com/kshitijzutshi/DAMG7245-Assignment-3-Repo/blob/main/docs/notebooks/GRETEL_create_synthetic_data_from_a_dataframe_or_csv.ipynb) ⭐
2. Design the JSON/YAML parameters file you plan to use
3. Design the python client to interface with the API


### Part 2: Designing the REST API

1. **Preparation**: Run the FastAPI tutorial shared on Canvas
2. The goal of this part is to implement a REST API to execute ONE of the models of your choice. The
model will take 13 images as input and 12 images as output. But the end user won’t pass the actual
images but will pass references that will be used by the backend to look for the input images.
3. **Design**: You will need to design
a. The JSON file (Blueprint) you will pass (using CURL or POSTMAN) to execute a model.
Make sure you document the blueprint well and add any default values.
b. The API - What operations will you support
c. Assumptions - Based on the use case (industry/govt etc), write down the assumptions you
have for the application
4. **Implementation:**
  a. Using the data science github template( or you can also see the gretel design). Implement
the REST API.

  b. Deploy this locally (using uvicorn) or on the cloud
(https://fastapi.tiangolo.com/deployment/deta/)

  c. Build test cases to illustrate how to use the API
  
  d. Write a Jupyter notebook that will illustrate how to invoke this api
  
