# FOODGRAM

Foodgram is a website where users can share recipes, save recipes from others as favorites, and subscribe to other authors' publications. Users also have access to a "Shopping List" feature to create a list of ingredients needed for selected recipes.


### Technologies Used
- Django
- Django Rest Framework
- Python
- PostgreSQL
- Djoser
- Docker

### Steps to Launch the Project on a Remote Server

```bash
# 1. Clone the Repository
git clone git@github.com:allkos/foodgram-project-react.git

# 2. Build Docker Images

# In the frontend directory
cd frontend
docker build -t <your_DockerHub_username>/<image_name> .

# In the backend directory
cd ../backend
docker build -t <your_DockerHub_username>/<image_name> .

# In the infra directory
cd ../infra
docker build -t <your_DockerHub_username>/<image_name> .

# 3. Push Images to Docker Hub
docker push <your_DockerHub_username>/<image_name>  # backend
docker push <your_DockerHub_username>/<image_name>  # frontend
docker push <your_DockerHub_username>/<image_name>  # gateway

# 4. Update Image Names in docker-compose.production.yml
# For each image, update the image: line to reflect <your_DockerHub_username>/<image_name>.

# 5. Install Docker Compose on the Server
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin

# 6. Copy docker-compose.production.yml to the Server
scp -i path_to_SSH/SSH_name docker-compose.production.yml \
    username@server_ip:/home/username/taski/docker-compose.production.yml

# Alternatively, edit the file directly using a text editor like nano.

# 7. Create an .env File
# In the project directory, create an .env file and populate it according to .env.example.

# 8. Run the Project in Detached Mode
sudo docker compose -f docker-compose.production.yml up -d

# 9. Run Migrations, Collect Static Files, and Populate Ingredients
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
