
from PIL import Image, ImageTk
image_width = 40
image_height = 40


from utils import resource_path
from pathlib import Path

model = Path(resource_path("images/model-algo.png"))
patient = Path(resource_path("images/patient.png"))
stats = Path(resource_path("images/stats-data.png"))
logout = Path(resource_path("images/logout.png"))
dbconnect = Path(resource_path("images/database.png"))
user = Path(resource_path("images/user-icon.png"))
chatbot_msg = Path(resource_path("images/chatbot.png"))




model_image = Image.open(model).resize(size =(image_width, image_height))
patient_image = Image.open(patient).resize(size =(image_width, image_height))
stats_image = Image.open(stats).resize(size =(image_width, image_height))
connect_db = Image.open(dbconnect).resize(size =(image_width, image_height))
logout_image = Image.open(logout).resize(size =(image_width, image_height))

user_image = Image.open(user).resize(size =(image_width, image_height))
chatbot_image = Image.open(chatbot_msg).resize(size =(image_width, image_height))


images = {
        'model_image': model_image, 
        'patient_image':patient_image, 
        'stats_image': stats_image, 
        'connectar': connect_db, 
        'chatbot':   chatbot_image, # the notification image is going to be added once created (dynamically)
        'logout_image':logout_image,
        
        }


