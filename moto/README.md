# MOTO

## Setup Instructions

### First-time Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/moto.git
   cd moto
   ```

2. Create a self-signed certificate:
   ```
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx-selfsigned.key -out nginx-selfsigned.crt
   ```

3. Copy the certificate files to the appropriate directories:
   ```
   cp nginx-selfsigned.key server/nginx/certificate/nginx-selfsigned.key
   cp nginx-selfsigned.crt server/nginx/certificate/nginx-selfsigned.crt
   cp nginx-selfsigned.key moto/certificate/nginx-selfsigned.key
   cp nginx-selfsigned.crt moto/certificate/nginx-selfsigned.crt
   ```

4. Create your environment file:
   ```
   cp .env.template .env
   ```
   Edit the `.env` file with your preferred settings.

5. Build and start the Docker containers:
   ```
   docker-compose up --build
   ```

### Accessing the Application

- **Django Admin**: https://localhost:8000/admin
- **Native App**: Will automatically start in its own window
- **API Documentation**: https://localhost:8000/api/docs/

### Creating an Admin User

1. With the server running, open a new terminal and run:
   ```
   docker-compose exec django python manage.py createsuperuser
   ```
   Follow the prompts to create your admin user.

2. You can now log in to the Django admin interface at https://localhost:8000/admin

### Importing User Data

1. Log in to the Django admin interface
2. Navigate to "CSV Import"
3. Upload your Excel (.xlsx) file
4. Select all four fields
5. Click "Upload File"
6. The system will download an Excel file with OTPs for the imported users

## Resetting the Database

If you encounter errors like 'relation does not exist' or 'column does not exist':

1. Open Docker Desktop
2. Go to Containers and locate MOTO
3. Expand MOTO and click on db-1
4. Go to the Exec tab
5. Run: `dropdb moto -f -U postgres`
6. Run: `createdb moto -U postgres`
7. In the project folder, delete all files in main_app/migrations except `__init__.py`
8. Restart the server with `docker-compose up`

## Development

### Directory Structure

- `moto/` - Main Django project
    - `api/` - API application
    - `main_app/` - Main Django application
    - `native_app/` - GTK application
- `server/` - Nginx server configuration

### Key API Endpoints

- `/api/login/` - User authentication
- `/api/rooms/` - List all rooms
- `/api/users/` - List all users
- `/api/students/register/` - Register student in room
- `/api/students/unregister/` - Unregister student from room

## Troubleshooting

### GTK Application Display Issues

For MacOS development:

1. `brew install xquartz`
2. `open -a XQuartz`
3. In the XQuartz terminal, run:
    - `xhost +`
    - `xhost +local:`

### Certificate Issues

If you encounter certificate validation errors, make sure:
1. The certificates are properly copied to both server/nginx/certificate/ and moto/certificate/
2. The certificates are valid and not expired
3. Your browser/system trusts the self-signed certificates

## License

This project is licensed under the GNU Affero General Public License v3.0.